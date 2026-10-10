"""Deterministic synthetic OHLCV for TESTS ONLY. No simulated return proves alpha."""
from __future__ import annotations
import numpy as np
import pandas as pd
import exchange_calendars as xcals
from .data import BarPanel, NY


def synthetic_panel(*, start='2026-08-31', end='2026-09-25', seed=22,
                    symbols=('SPY','QQQ','IWM','DIA','TLT','GLD')) -> BarPanel:
    c = xcals.get_calendar('XNYS')
    sessions = c.sessions_in_range(start,end)
    rng = np.random.default_rng(seed)
    n = len(symbols)
    current = 100 + 25*rng.random(n)
    # Market betas: the original six, then deterministic draws for larger universes.
    betas = np.r_[[1., 1.2, 1.4, 1.05, -.1, .3], np.random.default_rng(seed+1).uniform(-.2, 1.5, max(0, n-6))][:n]
    open_mat, close_mat, vol_mat, times = [], [], [], []
    for si,day in enumerate(sessions):
        interval = pd.date_range(c.session_open(day),c.session_close(day)-pd.Timedelta(minutes=5),freq='5min')
        # Changes in drift and correlations deliberately illustrate regime shift.
        base_drift = (-.00003 if si > len(sessions)//2 else .00003)
        overnight = rng.normal(0,.004,n)
        current = current*(1+overnight)
        for b,ts in enumerate(interval):
            market = rng.normal(base_drift,.0009)
            shocks = rng.normal(0,.0008,n)
            rets = market*betas + shocks
            if b == 0:
                rets *= 1.3
            op = current.copy()
            current = current * (1+rets)
            open_mat.append(op)
            close_mat.append(current.copy())
            vol_mat.append(rng.integers(20_000,120_000,n))
            times.append(ts)
    index = pd.DatetimeIndex(times)
    cols = list(symbols)
    return BarPanel(pd.DataFrame(open_mat,index=index,columns=cols),
                    pd.DataFrame(close_mat,index=index,columns=cols),
                    pd.DataFrame(vol_mat,index=index,columns=cols),
                    pd.Series(index.tz_convert(NY).strftime('%Y-%m-%d'),index=index),
                    {'source':'SYNTHETIC SIMULATED MARKET; NOT REAL DATA',
                     'calendar':'XNYS', 'sessions':len(sessions), 'timeframe':'5Min'})
