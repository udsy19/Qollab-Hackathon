"""Local Parquet cache of Alpaca 1-minute bars, its manifest, and completeness checks.

Layout of one cache directory (one feed x one adjustment mode; never mixed):

    manifest.json              provenance: request params, SHA-256 per file, timestamps
    minute/<SYMBOL>/<YYYY-MM>.parquet   raw 1Min bars, all hours Alpaca returned
    daily/<SYMBOL>.parquet     1Day bars, used only to cross-check minute volume
    bars_5min.parquet          5-minute bars from COMPLETE minutes only (data.aggregate_5min)
    validation.json            per symbol-session completeness, flags, rejected sessions

Time: every timestamp is a UTC bar START. Sessions, holidays, half days and DST
come from the exchange-calendars XNYS calendar; a partition is one New York
calendar month, bounded at New York midnight, so no session is split.
No credential is ever passed to, or written by, this module.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import exchange_calendars as xcals
import pandas as pd

from .data import file_sha256

NY = 'America/New_York'
SCHEMA_VERSION = 1
MINUTE_COLUMNS = ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume', 'trade_count', 'vwap']
SIP_RECENCY_DELAY = pd.Timedelta(minutes=16)   # Alpaca: no SIP inside the latest 15 minutes on Basic
GAP_FLAG = 0.15            # |open / previous close - 1| above this: possible unadjusted corporate action
VOLUME_RATIO_FLAG = (0.5, 1.5)


class DatasetIntegrityError(RuntimeError):
    """The cache on disk does not match its manifest. Never silently repaired on read."""


def calendar():
    return xcals.get_calendar('XNYS')


def utc_iso(ts: pd.Timestamp) -> str:
    return pd.Timestamp(ts).tz_convert('UTC').isoformat().replace('+00:00', 'Z')


def ny_midnight(day) -> pd.Timestamp:
    return pd.Timestamp(pd.Timestamp(day).date()).tz_localize(NY).tz_convert('UTC')


def latest_permitted_session(now: pd.Timestamp, cal=None) -> pd.Timestamp:
    """Latest XNYS session whose close is at least 16 minutes before `now`."""
    cal = cal or calendar()
    now = pd.Timestamp(now).tz_convert('UTC') if pd.Timestamp(now).tzinfo else pd.Timestamp(now).tz_localize('UTC')
    day = pd.Timestamp(now.tz_convert(NY).date())
    sessions = cal.sessions_in_range(day - pd.Timedelta(days=14), day)
    for ses in reversed(sessions):
        if cal.session_close(ses) + SIP_RECENCY_DELAY <= now:
            return ses
    raise ValueError('No completed XNYS session in the 14 days before now')


def download_end(now: pd.Timestamp, cal=None) -> tuple[pd.Timestamp, pd.Timestamp]:
    """(latest permitted session, exclusive UTC end of the download window)."""
    cal = cal or calendar()
    ses = latest_permitted_session(now, cal)
    end = min(ny_midnight(ses + pd.Timedelta(days=1)), pd.Timestamp(now) - SIP_RECENCY_DELAY)
    return ses, end


@dataclass(frozen=True)
class Partition:
    month: str
    start: pd.Timestamp
    end: pd.Timestamp


def month_partitions(start, end: pd.Timestamp) -> list[Partition]:
    """New York calendar months covering [start date at NY midnight, end)."""
    first = ny_midnight(start)
    end = pd.Timestamp(end)
    parts = []
    month = pd.Timestamp(pd.Timestamp(start).date()).to_period('M')
    while True:
        m_start = max(first, ny_midnight(month.start_time))
        if m_start >= end:
            break
        m_end = min(end, ny_midnight((month + 1).start_time))
        parts.append(Partition(str(month), m_start, m_end))
        month += 1
    return parts


def bar_request(symbol: str, start: pd.Timestamp, end: pd.Timestamp, *, feed: str,
                adjustment: str, timeframe: str = '1Min', limit: int = 10000) -> dict:
    """Exact query parameters for /v2/stocks/bars. Contains no credential."""
    return {'symbols': symbol, 'timeframe': timeframe, 'start': utc_iso(start), 'end': utc_iso(end),
            'limit': limit, 'feed': feed, 'adjustment': adjustment, 'sort': 'asc'}


def bars_to_frame(pages: list[dict], symbol: str) -> pd.DataFrame:
    """Alpaca page payloads -> typed frame. Rejects bars for an unrequested symbol."""
    rows = []
    for page in pages:
        extra = set(page) - {symbol}
        if extra:
            raise ValueError(f'Alpaca returned bars for unrequested symbols {sorted(extra)}')
        for b in page.get(symbol, []):
            rows.append((b['t'], symbol, b['o'], b['h'], b['l'], b['c'], b['v'], b.get('n'), b.get('vw')))
    df = pd.DataFrame(rows, columns=MINUTE_COLUMNS)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    for col in MINUTE_COLUMNS[2:]:
        df[col] = pd.to_numeric(df[col], errors='raise').astype('float64')
    if df.duplicated(['timestamp']).any():
        raise ValueError(f'{symbol}: duplicate bar timestamps across pages')
    return df.sort_values('timestamp').reset_index(drop=True)


def write_parquet(df: pd.DataFrame, path: Path) -> str:
    """Atomic write (temp file then rename); returns the SHA-256 of the bytes on disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.partial')
    df.to_parquet(tmp, index=False, engine='pyarrow', compression='zstd')
    os.replace(tmp, path)
    return file_sha256(path)


def write_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.partial')
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=False, default=str) + '\n')
    os.replace(tmp, path)


def read_manifest(cache_dir: Path) -> dict | None:
    p = Path(cache_dir) / 'manifest.json'
    return json.loads(p.read_text()) if p.exists() else None


def verify_entry(cache_dir: Path, entry: dict) -> bool:
    p = Path(cache_dir) / entry['path']
    return p.is_file() and file_sha256(p) == entry['sha256']


def load_dataset(cache_dir: Path, symbols: list[str] | None = None) -> pd.DataFrame:
    """Every minute partition in the manifest, SHA-256 verified, concatenated.

    A missing or altered file raises DatasetIntegrityError: a dataset is either
    exactly what the manifest says, or it is not used.
    """
    cache_dir = Path(cache_dir)
    man = read_manifest(cache_dir)
    if man is None:
        raise DatasetIntegrityError(f'No manifest.json in {cache_dir}; run qc_trade.fetch first')
    entries = [e for e in man['files'] if symbols is None or e['symbol'] in symbols]
    if not entries:
        raise DatasetIntegrityError('Manifest lists no minute files for the requested symbols')
    frames = []
    for e in entries:
        p = cache_dir / e['path']
        if not p.is_file():
            raise DatasetIntegrityError(f'Missing cached file {e["path"]}')
        if file_sha256(p) != e['sha256']:
            raise DatasetIntegrityError(f'sha256 mismatch for {e["path"]}: cache altered since download')
        frames.append(pd.read_parquet(p))
    return pd.concat(frames, ignore_index=True).sort_values(['timestamp', 'symbol']).reset_index(drop=True)


def validate_minutes(minutes: pd.DataFrame, daily: pd.DataFrame | None, symbols: list[str],
                     first_session, last_session, cal=None) -> dict:
    """Completeness, volume and corporate-action checks for every symbol x XNYS session.

    A session is REJECTED for a symbol when it has no regular-hours bars or any
    5-minute bucket lacks one of its five 1-minute bars: the same rule
    `data.aggregate_5min` applies with its default min_one_minute_bars=5.
    Flags (overnight gaps, daily-volume mismatch, bars on non-session dates) are
    reported, never acted on.
    """
    cal = cal or calendar()
    sessions = cal.sessions_in_range(pd.Timestamp(first_session), pd.Timestamp(last_session))
    m = minutes.copy()
    m['session'] = m['timestamp'].dt.tz_convert(NY).dt.strftime('%Y-%m-%d')
    session_names = {str(s.date()) for s in sessions}
    rows, rejected, flags = [], {}, []
    for day in sorted(set(m['session']) - session_names):
        for sym in sorted(set(m.loc[m.session.eq(day), 'symbol'])):
            flags.append({'flag': 'bars_on_non_session_date', 'symbol': sym, 'session': day,
                          'bars': int((m.session.eq(day) & m.symbol.eq(sym)).sum())})
    daily_vol = {}
    if daily is not None and len(daily):
        dd = daily.copy()
        dd['session'] = dd['timestamp'].dt.tz_convert(NY).dt.strftime('%Y-%m-%d')
        daily_vol = {(r.symbol, r.session): float(r.volume) for r in dd.itertuples()}
    by_key = {k: g for k, g in m.groupby(['symbol', 'session'])}
    for sym in symbols:
        prev_close = None
        for ses in sessions:
            day = str(ses.date())
            o, c = cal.session_open(ses), cal.session_close(ses)
            expected = int((c - o) / pd.Timedelta(minutes=1))
            g = by_key.get((sym, day))
            if g is None:
                g = m.iloc[0:0]
            reg = g[(g.timestamp >= o) & (g.timestamp < c)]
            buckets = ((reg.timestamp - o) // pd.Timedelta(minutes=5)).value_counts()
            n_buckets = expected // 5
            incomplete = n_buckets - int((buckets >= 5).sum())
            reg_vol = float(reg.volume.sum())
            dvol = daily_vol.get((sym, day))
            ratio = None if not dvol else reg_vol / dvol
            row = {'symbol': sym, 'session': day, 'open_utc': utc_iso(o), 'close_utc': utc_iso(c),
                   'expected_minutes': expected, 'regular_bars': int(len(reg)),
                   'missing_minutes': expected - int(len(reg)), 'incomplete_5m_buckets': incomplete,
                   'zero_volume_minutes': int((reg.volume == 0).sum()),
                   'extended_hours_bars': int(len(g) - len(reg)),
                   'regular_volume': reg_vol, 'daily_volume': dvol,
                   'volume_ratio': None if ratio is None else round(ratio, 6)}
            rows.append(row)
            if reg.empty:
                rejected.setdefault(day, {})[sym] = 'no regular-session bars'
            elif incomplete:
                rejected.setdefault(day, {})[sym] = (
                    f'{row["missing_minutes"]} missing minute(s); {incomplete} incomplete 5m bucket(s)')
            if ratio is not None and not VOLUME_RATIO_FLAG[0] <= ratio <= VOLUME_RATIO_FLAG[1]:
                flags.append({'flag': 'daily_volume_mismatch', 'symbol': sym, 'session': day,
                              'minute_over_daily_volume': round(ratio, 4)})
            if not reg.empty:
                first_open = float(reg.open.iloc[0])
                if prev_close is not None and abs(first_open / prev_close - 1) > GAP_FLAG:
                    flags.append({'flag': 'overnight_gap', 'symbol': sym, 'session': day,
                                  'open_over_prev_close': round(first_open / prev_close, 4),
                                  'note': 'possible unadjusted split/corporate action; inspect'})
                prev_close = float(reg.close.iloc[-1])
    expected_sessions = len(sessions)
    return {
        'calendar': 'XNYS', 'timezone': NY, 'timestamps': 'UTC bar start',
        'first_session': str(sessions[0].date()) if expected_sessions else None,
        'last_session': str(sessions[-1].date()) if expected_sessions else None,
        'expected_sessions': expected_sessions,
        'half_day_sessions': sorted({r['session'] for r in rows if r['expected_minutes'] < 390}),
        'rejection_rule': 'no regular bars, or any 5-minute bucket missing a 1-minute bar',
        'rejected_sessions': dict(sorted(rejected.items())),
        'rejected_session_count': len(rejected),
        'rejected_fraction': round(len(rejected) / expected_sessions, 6) if expected_sessions else None,
        'flags': flags,
        'sessions': rows,
    }


def five_minute_frame(panel) -> pd.DataFrame:
    """Long form of a data.BarPanel (open, close, volume per symbol x 5m bar start)."""
    parts = []
    for field in ('open', 'close', 'volume'):
        s = getattr(panel, field).stack()
        s.name = field
        parts.append(s)
    out = pd.concat(parts, axis=1).reset_index()
    out.columns = ['timestamp', 'symbol', 'open', 'close', 'volume']
    out['session'] = out['timestamp'].dt.tz_convert(NY).dt.strftime('%Y-%m-%d')
    return out.sort_values(['timestamp', 'symbol']).reset_index(drop=True)


def summarize_coverage(minutes: pd.DataFrame) -> dict:
    out = {}
    for sym, g in minutes.groupby('symbol'):
        out[sym] = {'rows': int(len(g)), 'first_utc': utc_iso(g.timestamp.min()),
                    'last_utc': utc_iso(g.timestamp.max())}
    return out


__all__ = ['DatasetIntegrityError', 'Partition', 'bar_request', 'bars_to_frame', 'calendar',
           'download_end', 'file_sha256', 'five_minute_frame', 'latest_permitted_session',
           'load_dataset', 'month_partitions', 'read_manifest', 'summarize_coverage',
           'validate_minutes', 'verify_entry', 'write_json', 'write_parquet']
