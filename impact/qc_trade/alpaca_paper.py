"""Credential-safe, strictly READ-ONLY Alpaca Paper & historical market-data access.

This module is the ONE HTTP path to Alpaca in QC-TRADE. It has no trading
endpoints, no write verbs, no secret serialization and no user-controlled
destination URLs: only GET on an allow-list of (host, path) pairs, never
following redirects, with exponential backoff on 429 and 5xx.
"""
from __future__ import annotations

import os
import time
from typing import Any, Callable, Iterator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PAPER_HOST = 'https://paper-api.alpaca.markets'
DATA_HOST = 'https://data.alpaca.markets'
# Exact read-only paths; anything else (orders, positions, the live host) is refused.
ALLOWED = {
    PAPER_HOST: {'/v2/account', '/v2/clock'},
    DATA_HOST: {'/v2/stocks/bars'},
}
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
FEEDS = ('sip', 'iex')


class AlpacaConnectionError(RuntimeError):
    """Sanitized failure with no credential or server-response echo."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def http_session() -> requests.Session:
    """Session with connection-level retries only.

    HTTP-status retries (429/5xx) are done explicitly in `_get_json`, so they are
    counted, logged and testable, and never stacked on top of adapter retries.
    """
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=Retry(
        total=3, connect=3, read=3, status=0, backoff_factor=1,
        allowed_methods=frozenset({'GET'}))))
    session.headers.update({'User-Agent': 'QC-TRADE-research/2.0'})
    return session


def _auth_session() -> requests.Session:
    key = os.environ.get('APCA_API_KEY_ID', '').strip()
    secret = os.environ.get('APCA_API_SECRET_KEY', '').strip()
    if not key or not secret:
        raise AlpacaConnectionError(
            'Missing Alpaca credentials. Set APCA_API_KEY_ID and '
            'APCA_API_SECRET_KEY as environment variables.')
    session = http_session()
    session.headers.update({
        'APCA-API-KEY-ID': key,
        'APCA-API-SECRET-KEY': secret,
    })
    return session


def _backoff_delay(attempt: int, response, base: float, cap: float) -> float:
    headers = getattr(response, 'headers', None) or {}
    retry_after = headers.get('Retry-After')
    if retry_after is not None:
        try:
            return min(cap, max(0.0, float(retry_after)))
        except ValueError:
            pass
    return min(cap, base * (2 ** attempt))


def _get_json(session, *, host: str, path: str, params: dict | None = None,
              max_attempts: int = 6, base_delay: float = 1.0, max_delay: float = 60.0,
              sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    if path not in ALLOWED.get(host, ()):
        raise ValueError('Only the official read-only Alpaca v2 endpoints are permitted')
    for attempt in range(max_attempts):
        try:
            # Do NOT follow 3xx redirects: custom credential headers could otherwise
            # be forwarded to an untrusted domain.
            response = session.get(host + path, params=params, timeout=30,
                                   allow_redirects=False)
        except requests.RequestException:
            raise AlpacaConnectionError(
                'Could not connect to the official Alpaca API. Check network, DNS, '
                'VPN/firewall and system time. No orders were sent.') from None
        status = response.status_code
        if status in RETRY_STATUSES and attempt < max_attempts - 1:
            sleep(_backoff_delay(attempt, response, base_delay, max_delay))
            continue
        break
    if status in (301, 302, 303, 307, 308):
        raise AlpacaConnectionError('Alpaca returned an unexpected redirect; stopped safely.', status)
    if status == 401:
        raise AlpacaConnectionError('HTTP 401: credentials are missing, revoked, or invalid.', status)
    if status == 403:
        raise AlpacaConnectionError(
            'HTTP 403: access forbidden; check market-data entitlement / feed.', status)
    if status == 429:
        raise AlpacaConnectionError(
            f'HTTP 429: Alpaca request rate limit still reached after {max_attempts} attempts.', status)
    if not 200 <= status < 300:
        raise AlpacaConnectionError(
            f'Alpaca read-only GET failed (HTTP {status}) after {attempt + 1} attempt(s).', status)
    try:
        result = response.json()
    except ValueError:
        raise AlpacaConnectionError('Alpaca returned invalid JSON.') from None
    if not isinstance(result, dict):
        raise AlpacaConnectionError('Unexpected Alpaca response format.')
    return result


def iter_bar_pages(session, params: dict, *,
                   sleep: Callable[[float], None] = time.sleep) -> Iterator[dict[str, list]]:
    """Yield the `bars` mapping of every page of one /v2/stocks/bars query.

    Follows `next_page_token` until it is empty; a repeated token is an error,
    never a silent truncation. `params` is updated in place with the token, so
    callers that record the request must copy it first.
    """
    seen: set[str] = set()
    while True:
        payload = _get_json(session, host=DATA_HOST, path='/v2/stocks/bars',
                            params=params, sleep=sleep)
        yield payload.get('bars') or {}
        token = payload.get('next_page_token')
        if not token:
            return
        if token in seen:
            raise AlpacaConnectionError('Alpaca repeated a pagination token; incomplete download stopped.')
        seen.add(token)
        params['page_token'] = token


def paper_account_summary(session, *, sleep=time.sleep) -> dict:
    """GET /v2/account and /v2/clock on the PAPER host; returns only non-identifying fields.

    Success proves the keys are paper keys: the paper host rejects live keys.
    """
    account = _get_json(session, host=PAPER_HOST, path='/v2/account', sleep=sleep)
    clock = _get_json(session, host=PAPER_HOST, path='/v2/clock', sleep=sleep)
    return {
        'paper_account_authenticated': True,
        'paper_only': True,
        'broker_orders_submitted': 0,
        'account_status': account.get('status'),
        'account_blocked': bool(account.get('account_blocked', False)),
        'trading_blocked': bool(account.get('trading_blocked', False)),
        'market_open': bool(clock.get('is_open', False)),
    }


def probe_feed(session, feed: str, start: str, end: str, *, symbol: str = 'SPY',
               sleep=time.sleep) -> tuple[str, int]:
    """Ask for <=5 one-minute bars on `feed`. Returns (status, bar_count).

    status is 'allowed' (bars returned), 'empty' (authorised but no bars),
    'forbidden' (HTTP 403: not entitled) or 'error-<http status>'.
    """
    if feed not in FEEDS:
        raise ValueError('Feed must be sip or iex')
    params = {'symbols': symbol, 'timeframe': '1Min', 'start': start, 'end': end,
              'feed': feed, 'limit': 5, 'adjustment': 'raw'}
    try:
        data = _get_json(session, host=DATA_HOST, path='/v2/stocks/bars', params=params, sleep=sleep)
    except AlpacaConnectionError as exc:
        if exc.status == 401:
            raise
        return ('forbidden' if exc.status == 403 else f'error-{exc.status}'), 0
    count = len((data.get('bars') or {}).get(symbol, []))
    return ('allowed' if count else 'empty'), count


def check_paper_and_data(*, feed: str = 'sip',
                         probe_start: str = '2025-09-10T00:00:00Z',
                         probe_end: str = '2025-09-11T00:00:00Z') -> dict:
    """Verify paper credentials and historical data using GET exclusively.

    Results intentionally omit account ID, dollar amounts and anything that
    could identify the account or disclose its credentials.
    """
    if feed not in FEEDS:
        raise ValueError('Feed must be sip or iex')
    session = _auth_session()
    summary = paper_account_summary(session)
    params = {
        'symbols': 'SPY', 'timeframe': '1Min',
        'start': probe_start, 'end': probe_end,
        'feed': feed, 'limit': 5, 'adjustment': 'raw',
    }
    data = _get_json(session, host=DATA_HOST, path='/v2/stocks/bars', params=params)
    count = len((data.get('bars') or {}).get('SPY', []))
    if count == 0:
        raise AlpacaConnectionError(
            'Authenticated, but market-data probe returned no SPY minute bars; '
            'check feed/date/entitlements.')
    return {
        **summary,
        'market_data_authenticated': True,
        'market_data_feed': feed,
        'market_data_probe_symbol': 'SPY',
        'market_data_probe_bar_count': count,
        'notes': 'GET requests only. SIP may require a historical data delay; IEX is only one exchange.',
    }
