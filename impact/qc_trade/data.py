"""Credited / user-licensed historical US equity minute bars, strict normalization.

The data contract uses a bar-start timestamp. Prices are RAW tradable prices,
not dividend-adjusted closes, because the simulated strategy ends each session flat.
No forward filling, no fabricated quotes, no cross-day price returns.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from io import TextIOWrapper
import hashlib
import csv
import json
import os
import re
import zipfile
import numpy as np
import pandas as pd
import exchange_calendars as xcals
from .alpaca_paper import http_session, iter_bar_pages

NY = 'America/New_York'
FIELDS = ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']
FREE_SAMPLE_URL = 'https://historicaldata.net/file/stocks_sample_2022H2.zip'


_OFFSET = r'(?:Z|[+-]\d{2}:?\d{2})$'


def parse_timestamps(col: pd.Series) -> pd.Series:
    """UTC timestamps, deciding time-zone awareness for EVERY row, not the first.

    All rows offset-aware (``Z`` / ``+hh:mm``): each is converted with its own
    offset, so -05:00 and -04:00 rows on either side of a DST change are both
    right. All rows naive: they are New York wall-clock times, localized with
    nonexistent/ambiguous DST times raising. A column mixing the two is refused.
    """
    if pd.api.types.is_datetime64_any_dtype(col):
        if getattr(col.dt, 'tz', None) is not None:
            return col.dt.tz_convert('UTC')
        return col.dt.tz_localize(NY, ambiguous='raise', nonexistent='raise').dt.tz_convert('UTC')
    aware = col.astype(str).str.strip().str.contains(_OFFSET, regex=True)
    if aware.all():
        return pd.to_datetime(col, utc=True, format='ISO8601')
    if aware.any():
        raise ValueError(f'timestamp column mixes timezone-aware and naive values '
                         f'({int(aware.sum())} aware, {int((~aware).sum())} naive); refusing to guess')
    return (pd.to_datetime(col, format='ISO8601')
            .dt.tz_localize(NY, ambiguous='raise', nonexistent='raise').dt.tz_convert('UTC'))


def normalize_minutes(df: pd.DataFrame) -> pd.DataFrame:
    missing = set(FIELDS) - set(df.columns)
    if missing:
        raise ValueError(f'Missing OHLCV columns: {sorted(missing)}')
    d = df[FIELDS].copy()
    d['symbol'] = d.symbol.astype(str).str.upper().str.strip()
    if (d.symbol.str.len() == 0).any():
        raise ValueError('Empty symbol')
    d['timestamp'] = parse_timestamps(d['timestamp'])
    for key in ('open', 'high', 'low', 'close', 'volume'):
        d[key] = pd.to_numeric(d[key], errors='raise')
    v = d[['open', 'high', 'low', 'close', 'volume']].to_numpy(float)
    if not np.isfinite(v).all() or (v[:, :4] <= 0).any() or (v[:, 4] < 0).any():
        raise ValueError('Nonfinite, nonpositive OHLC, or negative volume')
    if (d['high'] + 1e-8 < d[['open','close','low']].max(axis=1)).any():
        raise ValueError('High must bound other OHLC')
    if (d['low'] - 1e-8 > d[['open','close','high']].min(axis=1)).any():
        raise ValueError('Low must bound other OHLC')
    if d.duplicated(['timestamp','symbol']).any():
        raise ValueError('Duplicate symbol-minute bars')
    if not (d.timestamp.dt.second.eq(0) & d.timestamp.dt.microsecond.eq(0)).all():
        raise ValueError('Expected 1-minute bucket-start timestamps')
    return d.sort_values(['timestamp','symbol']).reset_index(drop=True)


def read_minute_csv(path: Path) -> pd.DataFrame:
    """Read 1-minute bars from a CSV, a Parquet file, or a verified cache directory.

    A directory must hold a `manifest.json` written by `qc_trade.fetch`; every
    partition is SHA-256 checked against it before use (see `dataset.load_dataset`).
    """
    path = Path(path)
    if path.is_dir():
        from .dataset import load_dataset
        return normalize_minutes(load_dataset(path))
    if path.suffix == '.parquet':
        return normalize_minutes(pd.read_parquet(path))
    return normalize_minutes(pd.read_csv(path))


def file_sha256(path: Path, *, chunk_size: int = 1 << 20) -> str:
    """Hash a large historical file without reading it entirely into memory.

    For a cache directory, the hash of its manifest stands for the dataset: the
    manifest pins the SHA-256 of every partition.
    """
    path = Path(path)
    if path.is_dir():
        path = path / 'manifest.json'
    hasher = hashlib.sha256()
    with Path(path).open('rb') as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_alpaca(symbols: list[str], start: str, end: str,
                    *, feed='sip', out: Path) -> dict:
    """Download genuine historical minute bars, AUTH from environment only.

    This is a pure read-only historical query against Alpaca's official data
    domain, NOT a broker-order API call. The output file is atomically published
    only after ALL API pages complete; an interruption leaves a .partial file.
    """
    key = os.getenv('APCA_API_KEY_ID')
    secret = os.getenv('APCA_API_SECRET_KEY')
    if not key or not secret:
        raise RuntimeError('Set APCA_API_KEY_ID and APCA_API_SECRET_KEY in your shell; no hardcoded credentials')
    if feed not in {'sip','iex'}:
        raise ValueError('feed must be sip or iex')
    if not symbols or len(symbols) != len(set(symbols)):
        raise ValueError('Symbols must be nonempty and unique')
    if any(not re.fullmatch(r'[A-Z0-9.\-]{1,16}', sym) for sym in symbols):
        raise ValueError('Invalid stock/ETF ticker name')
    beginning = pd.Timestamp(start)
    ending = pd.Timestamp(end)
    if beginning.tzinfo is None:
        beginning = beginning.tz_localize('UTC')
    else:
        beginning = beginning.tz_convert('UTC')
    if ending.tzinfo is None:
        ending = ending.tz_localize('UTC')
    else:
        ending = ending.tz_convert('UTC')
    if not beginning < ending:
        raise ValueError('Historical end must be after start')
    params = {'symbols':','.join(symbols),'timeframe':'1Min',
              'start':beginning.isoformat().replace('+00:00','Z'),
              'end':ending.isoformat().replace('+00:00','Z'),
              'limit':10000,'feed':feed,'adjustment':'raw','sort':'asc'}
    sess = http_session()
    sess.headers.update({'APCA-API-KEY-ID':key, 'APCA-API-SECRET-KEY':secret})
    pages, nrows = 0, 0
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    partial = out.with_name(out.name + '.partial')
    # Stream page-by-page rather than accumulating millions of records in RAM.
    # Pagination, backoff and the no-redirect rule live in alpaca_paper.iter_bar_pages.
    with partial.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for page in iter_bar_pages(sess, params):
            records = []
            for symbol, bars in page.items():
                for b in bars:
                    records.append({'timestamp':b['t'],'symbol':symbol,'open':b['o'],
                                    'high':b['h'],'low':b['l'],'close':b['c'],'volume':b['v']})
            if records:
                frame=normalize_minutes(pd.DataFrame(records))
                for record in frame.to_dict('records'):
                    record['timestamp']=record['timestamp'].isoformat()
                    writer.writerow(record)
                nrows += len(frame)
            pages += 1
    if nrows == 0:
        raise ValueError('Alpaca returned zero bars; check timestamps, entitlement and symbols')
    # Only expose a complete file; no credentials appear in data/provenance.
    partial.replace(out)
    meta = {'source':'Alpaca historical data API v2', 'feed':feed, 'adjustment':'raw',
            'symbols':symbols, 'start_utc':beginning.isoformat(), 'end_utc':ending.isoformat(),
            'rows':nrows, 'pages':pages, 'sha256':file_sha256(out)}
    out.with_suffix('.provenance.json').write_text(json.dumps(meta, indent=2))
    return meta


def download_public_sample(out: Path, *, symbols=('SPY','KO','TSLA','TWTR')) -> dict:
    """Download publisher's free, real, 2022H2 minute-bar sample.

    Source data are not redistributed in this project. The site must remain online
    for this convenience loader to work. Vendor's terms govern sample usage.
    """
    response = http_session().get(FREE_SAMPLE_URL, timeout=90)
    response.raise_for_status()
    from io import BytesIO
    frames = []
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        names = z.namelist()
        for symbol in symbols:
            matches = [x for x in names if x.lower().endswith('.csv') and 'minute_by_symbol' in x.lower()
                       and Path(x).name.upper().startswith(symbol.upper()+'_')]
            if not matches:
                # Some publisher samples may use flat paths; match only known symbol names.
                matches = [x for x in names if x.lower().endswith('.csv') and 'minute' in x.lower()
                           and Path(x).name.upper().startswith(symbol.upper()+'_')]
            if len(matches) != 1:
                raise ValueError(f'Expected one minute CSV for {symbol}; found {matches} (archive: {names[:12]})')
            with z.open(matches[0]) as member:
                df = pd.read_csv(member)
            if 'timestamp' not in df:
                raise ValueError(f'Archive minute format changed: {matches[0]} columns={list(df)}')
            df['symbol'] = symbol
            frames.append(df[FIELDS])
    result = normalize_minutes(pd.concat(frames, ignore_index=True))
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)
    meta = {'source':FREE_SAMPLE_URL, 'source_period':'July-December 2022',
            'symbols':list(symbols),'rows':len(result),
            'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
            'notice':'Historical data vendor sample; small pre-selected universe; insufficient for alpha claims'}
    out.with_suffix('.provenance.json').write_text(json.dumps(meta, indent=2))
    return meta


REJECTION_POLICY = ('drop the session for all symbols when any symbol has a 5-minute bucket with fewer '
                    'than min_one_minute_bars 1-minute bars; no fill, no partial sessions')


@dataclass
class BarPanel:
    open: pd.DataFrame
    close: pd.DataFrame
    volume: pd.DataFrame
    days: pd.Series           # UTC timestamp indexed -> New York session-date string
    diagnostics: dict


def aggregate_5min(minutes: pd.DataFrame, symbols: list[str], *, min_one_minute_bars: int=5,
                   max_missing_session_fraction: float=.15) -> BarPanel:
    """Drop incomplete days rather than fabricating prices or trading through gaps.

    Policy (REJECTION_POLICY): a 5-minute bar needs `min_one_minute_bars` of its
    five 1-minute bars; a session in which ANY symbol misses one is dropped for
    ALL symbols, so the panel is aligned and every kept session is the full XNYS
    5-minute grid (what backtest.validate_panel requires). The cost is selection
    bias towards calm days; it is measured, not hidden: `rejected_sessions`
    names every failing symbol with its reason, `per_symbol_completeness` counts
    them, and the fetch pipeline compares rejected vs kept daily ranges
    (dataset.selection_bias). Do not lower thresholds to keep more days.

    Uses XNYS exchange sessions (holidays + early closes) and UTC keys (DST).
    Timestamps are 5min bar starts, next-bar open is never used in features.
    Volume is observation, NOT necessarily consolidated all-exchange liquidity.
    """
    if not 1 <= min_one_minute_bars <= 5:
        raise ValueError('min_one_minute_bars must be 1..5')
    d = normalize_minutes(minutes)
    symbols = [x.upper() for x in symbols]
    if not symbols or len(symbols) != len(set(symbols)):
        raise ValueError('Provide distinct symbols')
    if set(symbols) - set(d.symbol.unique()):
        raise ValueError(f'Symbols without minutes: {set(symbols)-set(d.symbol.unique())}')
    c = xcals.get_calendar('XNYS')
    d = d[d.symbol.isin(symbols)].copy()
    ny_date = d.timestamp.dt.tz_convert(NY).dt.strftime('%Y-%m-%d')
    d['_session'] = ny_date
    begin, finish = ny_date.min(), ny_date.max()
    sessions = c.sessions_in_range(begin, finish)
    expected_dates = [str(x.date()) for x in sessions]
    frames, skipped = [], {}
    complete = {sym: 0 for sym in symbols}
    for session in sessions:
        day = str(session.date())
        day_df = d.loc[d['_session'].eq(day)]
        market_open = c.session_open(session)
        market_close = c.session_close(session)
        labels = pd.date_range(market_open, market_close-pd.Timedelta(minutes=5), freq='5min')
        if day_df.empty:
            skipped[day] = {sym: 'no bars' for sym in symbols}
            continue
        results, failures = [], {}
        for sym in symbols:
            bars = day_df.loc[day_df.symbol.eq(sym)].set_index('timestamp').sort_index()
            bars = bars.loc[(bars.index >= market_open) & (bars.index < market_close)]
            grouped = bars[['open','high','low','close','volume']].resample('5min', origin=market_open,
                            label='left', closed='left').agg({'open':'first','high':'max','low':'min',
                                                              'close':'last','volume':'sum'})
            counts = bars.close.resample('5min', origin=market_open, label='left', closed='left').count()
            valid = counts.reindex(labels, fill_value=0).ge(min_one_minute_bars)
            if not valid.all():
                failures[sym] = f'{int((~valid).sum())} of {len(labels)} 5m bars incomplete or missing'
                continue
            complete[sym] += 1
            grouped = grouped.reindex(labels)
            grouped['symbol'] = sym
            grouped['timestamp'] = labels
            grouped['_session'] = day
            results.append(grouped.reset_index(drop=True))
        if failures:
            skipped[day] = failures
        else:
            frames.extend(results)
    if not frames:
        raise ValueError(f'No complete shared trading sessions. Days rejected: {list(skipped.items())[:4]}; ' +
                         'IEX is sparse; SIP data or lower min_one_minute_bars may be needed')
    share = len(skipped) / max(1, len(expected_dates))
    if share > max_missing_session_fraction:
        raise ValueError(f'Rejected {len(skipped)}/{len(expected_dates)} sessions ({share:.1%}), ' +
                         'above allowed max_missing_session_fraction. Inspect missing bars; do not silently bias sample. ' +
                         f'Examples: {list(skipped.items())[:6]}')
    all_bars = pd.concat(frames, ignore_index=True)
    mats = {}
    for field in ['open','close','volume']:
        mat = all_bars.pivot(index='timestamp', columns='symbol', values=field)[symbols]
        if mat.isna().any().any() or mat.empty:
            raise RuntimeError('Invalid alignment after session filtering')
        mats[field] = mat
    ix = mats['close'].index
    days = pd.Series(ix.tz_convert(NY).strftime('%Y-%m-%d'), index=ix)
    return BarPanel(mats['open'], mats['close'], mats['volume'], days,
                    {'calendar':'XNYS', 'timezone':'America/New_York',
                     'timeframe':'5Min', 'min_one_minute_bars':min_one_minute_bars,
                     'session_count':len(expected_dates), 'kept_sessions':len(expected_dates)-len(skipped),
                     'rejected_sessions':skipped, 'rejection_policy':REJECTION_POLICY,
                     'per_symbol_completeness':{sym: {'complete_sessions': complete[sym],
                                                      'incomplete_sessions': len(expected_dates) - complete[sym]}
                                                for sym in symbols},
                     'symbols':symbols,'first_utc':ix[0].isoformat(), 'last_utc':ix[-1].isoformat()})


def read_panel_csv(path: Path, symbols: list[str], **kwargs) -> BarPanel:
    return aggregate_5min(read_minute_csv(path), symbols, **kwargs)
