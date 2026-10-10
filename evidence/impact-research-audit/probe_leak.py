"""Probe: does perturbing FUTURE bars change anything observed BEFORE the cut?
Uses only outputs the unmodified engine already produces (equity, orders, forecasts)."""
import sys
import numpy as np
import pandas as pd
from qc_trade.demo import synthetic_panel
from qc_trade.data import BarPanel
from qc_trade.optimizer import OptConfig
from qc_trade.backtest import ExecutionConfig, run_backtest, METHODS

p = synthetic_panel(start='2026-09-01', end='2026-09-15', symbols=('SPY', 'QQQ', 'IWM', 'DIA'))
cfg = ExecutionConfig(test_start='2026-09-09', history_bars=40, max_participation=1.)
o = OptConfig(k=2, anneal_steps=60, anneal_restarts=2)
ms = list(METHODS)
a = run_backtest(p, cfg, o, ms)
bad = 0
for cut in ['2026-09-10T15:02:00Z', '2026-09-11T13:30:00Z', '2026-09-14T19:00:00Z']:
    cut = pd.Timestamp(cut)
    rng = np.random.default_rng(1)
    later = p.close.index >= cut
    sh = (int(later.sum()), p.close.shape[1])
    no, nc, nv = p.open.copy(), p.close.copy(), p.volume.astype(float)
    no.loc[later] *= np.exp(rng.normal(0, .03, sh))
    nc.loc[later] *= np.exp(rng.normal(0, .03, sh))
    nv.loc[later] *= rng.uniform(.01, 5, sh)
    b = run_backtest(BarPanel(no, nc, nv, p.days, p.diagnostics), cfg, o, ms)
    eq_ok = a.equity.loc[a.equity.index < cut].equals(b.equity.loc[b.equity.index < cut])
    oa = a.orders[pd.to_datetime(a.orders.timestamp, utc=True) < cut].reset_index(drop=True)
    ob = b.orders[pd.to_datetime(b.orders.timestamp, utc=True) < cut].reset_index(drop=True)
    fa = a.forecasts[pd.to_datetime(a.forecasts.time_utc, utc=True) <= cut].reset_index(drop=True)
    fb = b.forecasts[pd.to_datetime(b.forecasts.time_utc, utc=True) <= cut].reset_index(drop=True)
    print(cut, 'equity_before_cut_equal', eq_ok, 'orders_equal', oa.equals(ob), len(oa),
          'forecasts_equal', fa.equals(fb), len(fa))
    bad += not (eq_ok and oa.equals(ob) and fa.equals(fb))
print('LEAK_FOUND' if bad else 'NO_LEAK_DETECTED')
sys.exit(1 if bad else 0)
