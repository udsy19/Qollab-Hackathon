"""Timing only: validate_minutes + aggregate_5min on a full-size frame (6 symbols, 2024-01..2026-10).

The frame is synthetic and exists only to measure runtime/memory of the pipeline's
post-download steps; it is never written to the cache and is not market data.
"""
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, sys.argv[1])
from qc_trade import dataset as ds  # noqa: E402
from qc_trade.data import aggregate_5min  # noqa: E402

cal = ds.calendar()
sessions = cal.sessions_in_range('2024-01-02', '2026-10-09')
idx = []
for s in sessions:
    o, c = cal.session_open(s), cal.session_close(s)
    idx.append(pd.date_range(o - pd.Timedelta(hours=5, minutes=30), c + pd.Timedelta(hours=4), freq='min',
                             inclusive='left'))
times = idx[0].append(idx[1:])
syms = ['SPY', 'QQQ', 'IWM', 'DIA', 'TLT', 'GLD']
frames = []
for s in syms:
    n = len(times)
    frames.append(pd.DataFrame({'timestamp': times, 'symbol': s, 'open': 100.0, 'high': 100.1, 'low': 99.9,
                                'close': 100.0, 'volume': 1000.0, 'trade_count': 5.0, 'vwap': 100.0}))
m = pd.concat(frames, ignore_index=True)
print('rows', len(m), 'sessions', len(sessions))
t = time.perf_counter()
v = ds.validate_minutes(m, None, syms, sessions[0], sessions[-1], cal)
print('validate_minutes s', round(time.perf_counter() - t, 1), 'rejected', v['rejected_session_count'])
t = time.perf_counter()
p = aggregate_5min(m, syms, max_missing_session_fraction=1.0)
print('aggregate_5min s', round(time.perf_counter() - t, 1), 'kept', p.diagnostics['kept_sessions'])
t = time.perf_counter()
f = ds.five_minute_frame(p)
print('five_minute_frame s', round(time.perf_counter() - t, 1), 'rows', len(f))
