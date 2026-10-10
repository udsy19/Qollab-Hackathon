"""`python -m qc_trade.fetch` - build the verified local 1-minute dataset from Alpaca.

Read-only: GET /v2/account and /v2/clock on the PAPER host (proves paper keys),
a 5-bar entitlement probe of BOTH feeds, then paginated GET /v2/stocks/bars per
symbol x New York month. Writes a Parquet cache plus manifest (see dataset.py).

Never: submits orders, contacts the live trading host, switches feed on its own,
substitutes synthetic data, prints or stores credentials. Credentials are read
from APCA_API_KEY_ID / APCA_API_SECRET_KEY only (scripts/fetch_real_data.sh
prompts for them with echo off).
"""
from __future__ import annotations

import argparse
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

from . import alpaca_paper as ap
from . import dataset as ds
from .data import aggregate_5min

UNIVERSE = 'SPY,QQQ,IWM,DIA,TLT,GLD'
ADJUSTMENTS = ('raw', 'split', 'dividend', 'all')


class FetchError(RuntimeError):
    def __init__(self, message: str, code: int = 1):
        super().__init__(message)
        self.code = code


def _now_utc() -> str:
    return pd.Timestamp.now(tz='UTC').isoformat()


def _code_version() -> str | None:
    try:
        out = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True,
                             cwd=Path(__file__).parent, timeout=10)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _parse(argv):
    p = argparse.ArgumentParser(prog='python -m qc_trade.fetch',
                                description='Read-only Alpaca historical 1Min download into a verified Parquet cache.')
    p.add_argument('--symbols', default=UNIVERSE)
    p.add_argument('--start', default='2024-01-01',
                   help='first New York date, inclusive: YYYY-MM-DD, or -Nd = N calendar days before '
                        'the latest permitted session (write --start=-28d)')
    p.add_argument('--feed', choices=ap.FEEDS, default='sip',
                   help='never switched automatically; a non-entitled feed is a failure')
    p.add_argument('--adjustment', choices=ADJUSTMENTS, default='raw',
                   help='Alpaca corporate-action adjustment; raw = tradable prices (see README)')
    p.add_argument('--cache-dir', default=None,
                   help='default: data/alpaca_<mode>_<feed>_<adjustment>_1min (gitignored)')
    p.add_argument('--mode', default='custom', help='label recorded in the manifest (pilot|full)')
    p.add_argument('--page-limit', type=int, default=10000)
    p.add_argument('--min-minute-bars', type=int, default=5,
                   help='1-minute bars required per 5-minute bar (1..5); 5 = complete minutes only. '
                        'Recorded in the manifest; lowering it is a research decision, not a fix')
    p.add_argument('--now', default=None, help='override the clock (tests / reproducing a past run)')
    p.add_argument('--dry-run', action='store_true',
                   help='print every request that would be made; no network, no credentials')
    a = p.parse_args(argv)
    a.symbols = [s.strip().upper() for s in a.symbols.split(',') if s.strip()]
    if not a.symbols or len(a.symbols) != len(set(a.symbols)):
        p.error('symbols must be non-empty and unique')
    if not 1 <= a.min_minute_bars <= 5:
        p.error('--min-minute-bars must be 1..5')
    if not 1 <= a.page_limit <= 10000:
        p.error('--page-limit must be 1..10000')
    a.cache_dir = Path(a.cache_dir or f'data/alpaca_{a.mode}_{a.feed}_{a.adjustment}_1min')
    return a


def _plan(a):
    now = pd.Timestamp(a.now) if a.now else pd.Timestamp.now(tz='UTC')
    if now.tzinfo is None:
        now = now.tz_localize('UTC')
    cal = ds.calendar()
    latest, end = ds.download_end(now, cal)
    rel = re.fullmatch(r'-(\d{1,4})d', a.start.strip())
    start = (pd.Timestamp(latest.date()) - pd.Timedelta(days=int(rel.group(1)))) if rel else pd.Timestamp(a.start)
    if ds.ny_midnight(start) >= end:
        raise FetchError(f'start {a.start} is not before the latest permitted session {latest.date()}', 2)
    parts = ds.month_partitions(start, end)
    requests = [(sym, part, ds.bar_request(sym, part.start, part.end, feed=a.feed,
                                           adjustment=a.adjustment, limit=a.page_limit))
                for sym in a.symbols for part in parts]
    probe_open = cal.session_open(latest)
    probe = (ds.utc_iso(probe_open), ds.utc_iso(probe_open + pd.Timedelta(minutes=10)))
    return cal, now, latest, start, end, requests, probe


def _query(params: dict) -> str:
    return '&'.join(f'{k}={v}' for k, v in params.items())


def dry_run(a) -> int:
    cal, now, latest, start, end, requests, probe = _plan(a)
    man = ds.read_manifest(a.cache_dir) if a.cache_dir.exists() else None
    cached = {(e['symbol'], e['month']): e for e in (man or {}).get('files', [])}
    skip = [r for r in requests if (r[0], r[1].month) in cached
            and cached[(r[0], r[1].month)]['request'] == r[2] and ds.verify_entry(a.cache_dir, cached[(r[0], r[1].month)])]
    print('DRY RUN - no network calls, no credentials read, nothing written.')
    print(f'clock: {now.isoformat()}  latest permitted XNYS session: {latest.date()}')
    print(f'window: {start.date()} .. {latest.date()}  (UTC {ds.utc_iso(ds.ny_midnight(start))} .. {ds.utc_iso(end)})')
    print(f'feed: {a.feed} (never switched)  adjustment: {a.adjustment}  symbols: {",".join(a.symbols)}')
    print(f'cache: {a.cache_dir}')
    print(f'GET {ap.PAPER_HOST}/v2/account   (paper host only; fields kept: status/blocked flags)')
    print(f'GET {ap.PAPER_HOST}/v2/clock')
    for feed in ap.FEEDS:
        print(f'GET {ap.DATA_HOST}/v2/stocks/bars?symbols=SPY&timeframe=1Min&start={probe[0]}&end={probe[1]}'
              f'&feed={feed}&limit=5&adjustment=raw   (entitlement probe)')
    print(f'minute-bar partitions to download: {len(requests) - len(skip)}  (already cached and verified: {len(skip)})')
    for sym, part, params in requests:
        if (sym, part, params) not in skip:
            print(f'GET {ap.DATA_HOST}/v2/stocks/bars?{_query(params)}  (+page_token until exhausted)')
    for sym in a.symbols:
        params = ds.bar_request(sym, ds.ny_midnight(start), end, feed=a.feed, adjustment=a.adjustment,
                                timeframe='1Day')
        print(f'GET {ap.DATA_HOST}/v2/stocks/bars?{_query(params)}  (daily volume cross-check)')
    return 0


def _download_partition(session, sym, part, params, cal, sleep) -> tuple[pd.DataFrame, int]:
    pages = list(ap.iter_bar_pages(session, dict(params), sleep=sleep))
    frame = ds.bars_to_frame(pages, sym)
    sessions = cal.sessions_in_range(part.start.tz_convert(ds.NY).date(),
                                     (part.end - pd.Timedelta(seconds=1)).tz_convert(ds.NY).date())
    if frame.empty and len(sessions):
        raise FetchError(f'{sym} {part.month}: Alpaca returned zero bars for {len(sessions)} '
                         'XNYS session(s); refusing to cache an empty month', 1)
    return frame, len(pages)


def run(a, sleep=time.sleep) -> int:
    cal, now, latest, start, end, requests, probe = _plan(a)
    try:
        session = ap._auth_session()
    except ap.AlpacaConnectionError as exc:
        raise FetchError(str(exc), 2) from None
    started = _now_utc()

    account = ap.paper_account_summary(session, sleep=sleep)
    print(f'[1/5] paper account authenticated: status={account["account_status"]} '
          f'trading_blocked={account["trading_blocked"]}  orders submitted: 0')

    entitlement = {'probe_session': str(latest.date()), 'probe_symbol': 'SPY'}
    for feed in ap.FEEDS:
        entitlement[feed], _ = ap.probe_feed(session, feed, *probe, sleep=sleep)
    print(f'[2/5] feed entitlement at {latest.date()}: sip={entitlement["sip"]} iex={entitlement["iex"]}; '
          f'requested feed: {a.feed}')
    if entitlement[a.feed] != 'allowed':
        others = [f for f in ap.FEEDS if f != a.feed and entitlement[f] == 'allowed']
        hint = f' Feed(s) that answered: {others}; rerun explicitly with --feed {others[0]} if that is acceptable.' if others else ''
        raise FetchError(f'Requested feed {a.feed!r} is {entitlement[a.feed]} for this account at '
                         f'{latest.date()}. Not switching feeds automatically.{hint}', 3)

    a.cache_dir.mkdir(parents=True, exist_ok=True)
    man = ds.read_manifest(a.cache_dir)
    if man and (man['feed'], man['adjustment']) != (a.feed, a.adjustment):
        raise FetchError('cache directory holds a different feed/adjustment; use another --cache-dir', 2)
    man = man or {'schema_version': ds.SCHEMA_VERSION, 'created_utc': started, 'files': []}
    man.update({
        'dataset': 'alpaca-us-equities-1min', 'status': 'incomplete', 'mode': a.mode,
        'source': 'Alpaca Market Data API v2, GET /v2/stocks/bars (historical)',
        'data_host': ap.DATA_HOST, 'paper_host': ap.PAPER_HOST,
        'feed': a.feed, 'adjustment': a.adjustment, 'timeframe': '1Min', 'symbols': a.symbols,
        'requested_start': str(start.date()), 'latest_permitted_session': str(latest.date()),
        'window_start_utc': ds.utc_iso(ds.ny_midnight(start)), 'window_end_utc': ds.utc_iso(end),
        'calendar': 'XNYS (exchange-calendars)', 'timezone': ds.NY, 'timestamp_convention': 'UTC bar start',
        'run_started_utc': started, 'run_clock_utc': now.isoformat(),
        'code_version': _code_version(),
        'software': {'python': platform.python_version(), 'pandas': pd.__version__,
                     'pyarrow': __import__('pyarrow').__version__,
                     'exchange_calendars': __import__('exchange_calendars').__version__},
        'paper_account': account, 'entitlement': entitlement,
        'credentials_recorded': False,
    })
    files = {(e['symbol'], e['month']): e for e in man['files']}
    print(f'[3/5] minute bars: {len(requests)} symbol-month partitions -> {a.cache_dir}')
    fetched = 0
    for sym, part, params in requests:
        old = files.get((sym, part.month))
        if old and old['request'] == params and ds.verify_entry(a.cache_dir, old):
            continue
        frame, pages = _download_partition(session, sym, part, params, cal, sleep)
        rel = f'minute/{sym}/{part.month}.parquet'
        sha = ds.write_parquet(frame, a.cache_dir / rel)
        files[(sym, part.month)] = {
            'path': rel, 'symbol': sym, 'month': part.month, 'rows': int(len(frame)), 'pages': pages,
            'first_utc': ds.utc_iso(frame.timestamp.min()) if len(frame) else None,
            'last_utc': ds.utc_iso(frame.timestamp.max()) if len(frame) else None,
            'sha256': sha, 'request': params, 'downloaded_utc': _now_utc()}
        man['files'] = sorted(files.values(), key=lambda e: (e['symbol'], e['month']))
        ds.write_json(man, a.cache_dir / 'manifest.json')   # resumable after every partition
        fetched += 1
        print(f'      {sym} {part.month}: {len(frame)} bars in {pages} page(s)')
    print(f'      downloaded {fetched}, reused {len(requests) - fetched} verified partition(s)')

    daily_frames, daily_entries = [], []
    for sym in a.symbols:
        params = ds.bar_request(sym, ds.ny_midnight(start), end, feed=a.feed,
                                adjustment=a.adjustment, timeframe='1Day')
        pages = list(ap.iter_bar_pages(session, dict(params), sleep=sleep))
        frame = ds.bars_to_frame(pages, sym)
        rel = f'daily/{sym}.parquet'
        daily_entries.append({'path': rel, 'symbol': sym, 'rows': int(len(frame)), 'pages': len(pages),
                              'sha256': ds.write_parquet(frame, a.cache_dir / rel), 'request': params,
                              'downloaded_utc': _now_utc()})
        daily_frames.append(frame)
    man['daily_files'] = daily_entries
    print(f'[4/5] daily bars for volume cross-check: {sum(e["rows"] for e in daily_entries)} rows')

    minutes = ds.load_dataset(a.cache_dir, a.symbols)
    lo = ds.ny_midnight(start)
    minutes = minutes[(minutes.timestamp >= lo) & (minutes.timestamp < end)].reset_index(drop=True)
    validation = ds.validate_minutes(minutes, pd.concat(daily_frames, ignore_index=True), a.symbols,
                                     start, latest, cal, min_one_minute_bars=a.min_minute_bars)
    ds.write_json(validation, a.cache_dir / 'validation.json')
    panel = aggregate_5min(minutes, a.symbols, min_one_minute_bars=a.min_minute_bars,
                           max_missing_session_fraction=1.0)
    five = ds.five_minute_frame(panel)
    kept = set(five.session)
    expected_kept = {r['session'] for r in validation['sessions']} - set(validation['rejected_sessions'])
    if kept != expected_kept:
        raise FetchError('5-minute reconstruction and the completeness report disagree on '
                         f'{sorted(kept ^ expected_kept)[:5]}; refusing to publish', 1)
    man['bars_5min'] = {'path': 'bars_5min.parquet', 'rows': int(len(five)), 'sessions': len(kept),
                        'rule': panel.diagnostics['rejection_policy'],
                        'min_one_minute_bars': a.min_minute_bars,
                        'sha256': ds.write_parquet(five, a.cache_dir / 'bars_5min.parquet')}
    man['validation'] = {'path': 'validation.json',
                         'sha256': ds.file_sha256(a.cache_dir / 'validation.json'),
                         'expected_sessions': validation['expected_sessions'],
                         'min_one_minute_bars': a.min_minute_bars,
                         'rejected_session_count': validation['rejected_session_count'],
                         'per_symbol_rejected': validation['per_symbol_rejected'],
                         'rejected_more_volatile_p_lt_0_05':
                             validation['selection_bias']['rejected_more_volatile_p_lt_0_05'],
                         'rejected_fraction': validation['rejected_fraction'],
                         'half_day_sessions': len(validation['half_day_sessions']),
                         'flag_count': len(validation['flags'])}
    man['coverage'] = ds.summarize_coverage(minutes)
    man['status'] = 'complete'
    man['run_finished_utc'] = _now_utc()
    ds.write_json(man, a.cache_dir / 'manifest.json')
    print(f'[5/5] validation: {validation["expected_sessions"]} sessions, '
          f'{validation["rejected_session_count"]} rejected ({validation["rejected_fraction"]:.2%}), '
          f'{len(validation["flags"])} flag(s); 5-minute bars kept for {len(kept)} sessions')
    print(f'      rejected per symbol: {validation["per_symbol_rejected"]}; rejected sessions more volatile '
          f'(p<0.05): {validation["selection_bias"]["rejected_more_volatile_p_lt_0_05"] or "none"}')
    print(f'use it: python -m qc_trade.cli backtest --data {a.cache_dir} ...   (no orders were submitted)')
    print(f'SUMMARY: OK mode={a.mode} feed={a.feed} adjustment={a.adjustment} symbols={len(a.symbols)} '
          f'window={start.date()}..{latest.date()} sessions={validation["expected_sessions"]} '
          f'rejected={validation["rejected_session_count"]} minute_rows={len(minutes)} '
          f'manifest={a.cache_dir / "manifest.json"} sha256={ds.file_sha256(a.cache_dir / "manifest.json")} orders=0')
    return 0


def main(argv=None, sleep=time.sleep) -> int:
    a = _parse(argv)
    try:
        return dry_run(a) if a.dry_run else run(a, sleep=sleep)
    except FetchError as exc:
        print(f'FAILED: {exc}', file=sys.stderr)
        return exc.code
    except (ap.AlpacaConnectionError, ds.DatasetIntegrityError, ValueError) as exc:
        print(f'FAILED: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
