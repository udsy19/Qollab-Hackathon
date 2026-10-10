"""Credential-safe, strictly READ-ONLY Alpaca Paper & historical market-data checks.

This module has no trading endpoints, no .post, no secret serialization,
no user-controlled destination URLs, and no write operations to the broker.
"""
from __future__ import annotations

import os
from typing import Any

import requests

from .data import http_session

PAPER_HOST = 'https://paper-api.alpaca.markets'
DATA_HOST = 'https://data.alpaca.markets'


class AlpacaConnectionError(RuntimeError):
    """Sanitized connection failures with no credential or server-response echo."""


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


def _get_json(session: requests.Session, *, host: str, path: str,
              params: dict | None = None) -> dict[str, Any]:
    if host not in (PAPER_HOST, DATA_HOST) or not path.startswith('/v2/'):
        raise ValueError('Only official Alpaca v2 endpoints are permitted')
    try:
        # Do NOT follow 3xx redirects: custom credential headers could otherwise
        # be forwarded to an untrusted domain.
        response = session.get(host + path, params=params, timeout=30,
                               allow_redirects=False)
    except requests.RequestException as exc:
        raise AlpacaConnectionError(
            'Could not connect to the official Alpaca API. Check network, DNS, '
            'VPN/firewall and system time. No orders were sent.') from None
    if response.status_code in (301, 302, 303, 307, 308):
        raise AlpacaConnectionError('Alpaca returned an unexpected redirect; stopped safely.')
    if response.status_code == 401:
        raise AlpacaConnectionError('HTTP 401: credentials are missing, revoked, or invalid.')
    if response.status_code == 403:
        raise AlpacaConnectionError(
            'HTTP 403: access forbidden; check market-data entitlement / feed.')
    if response.status_code == 429:
        raise AlpacaConnectionError('HTTP 429: Alpaca request rate limit reached.')
    if not response.ok:
        raise AlpacaConnectionError(
            f'Alpaca read-only GET failed (HTTP {response.status_code}).')
    try:
        result = response.json()
    except ValueError:
        raise AlpacaConnectionError('Alpaca returned invalid JSON.') from None
    if not isinstance(result, dict):
        raise AlpacaConnectionError('Unexpected Alpaca response format.')
    return result


def check_paper_and_data(*, feed: str = 'sip',
                         probe_start: str = '2025-09-10T00:00:00Z',
                         probe_end: str = '2025-09-11T00:00:00Z') -> dict:
    """Verify paper credentials and historical data using GET exclusively.

    Results intentionally omit account ID, dollar amounts and anything that
    could identify the account or disclose its credentials.
    """
    if feed not in {'sip', 'iex'}:
        raise ValueError('Feed must be sip or iex')
    session = _auth_session()
    account = _get_json(session, host=PAPER_HOST, path='/v2/account')
    clock = _get_json(session, host=PAPER_HOST, path='/v2/clock')
    params = {
        'symbols': 'SPY', 'timeframe': '1Min',
        'start': probe_start, 'end': probe_end,
        'feed': feed, 'limit': 5, 'adjustment': 'raw',
    }
    data = _get_json(session, host=DATA_HOST, path='/v2/stocks/bars',
                     params=params)
    count = len(data.get('bars', {}).get('SPY', []))
    if count == 0:
        raise AlpacaConnectionError(
            'Authenticated, but market-data probe returned no SPY minute bars; '
            'check feed/date/entitlements.')
    return {
        'paper_account_authenticated': True,
        'paper_only': True,
        'broker_orders_submitted': 0,
        'account_status': account.get('status'),
        'account_blocked': bool(account.get('account_blocked', False)),
        'trading_blocked': bool(account.get('trading_blocked', False)),
        'market_open': bool(clock.get('is_open', False)),
        'market_data_authenticated': True,
        'market_data_feed': feed,
        'market_data_probe_symbol': 'SPY',
        'market_data_probe_bar_count': count,
        'notes': 'GET requests only. SIP may require a historical data delay; IEX is only one exchange.',
    }
