"""Probe suspected defects on the unmodified tree. Each line prints DEFECT or OK."""
from dataclasses import replace
import numpy as np
import pandas as pd
from qc_trade.demo import synthetic_panel
from qc_trade.data import BarPanel
from qc_trade.optimizer import OptConfig
from qc_trade.backtest import ExecutionConfig, run_backtest

p = synthetic_panel(start='2026-09-01', end='2026-09-15', symbols=('SPY', 'QQQ', 'IWM', 'DIA'))
cfg = ExecutionConfig(test_start='2026-09-09', history_bars=40, max_participation=1.)
o = OptConfig(k=2)

# 1. A panel with a missing mid-session bar (a halt / data hole) must be refused.
keep = np.ones(len(p.close), bool)
keep[500] = False
holed = BarPanel(p.open[keep], p.close[keep], p.volume[keep], p.days[keep], p.diagnostics)
try:
    run_backtest(holed, cfg, o, ['spy', 'topk'])
    print('DEFECT 1: panel with a missing mid-session 5m bar accepted silently')
except ValueError as e:
    print('OK 1:', e)

# 2. The CLI --stress grid: README says '--stress-bps' is ADDITIONAL slippage per side.
#    cli.py does replace(exec_cfg, slippage_bps=slip): stress 0 must equal the base run.
base = run_backtest(p, cfg, o, ['topk'])
stress0 = run_backtest(p, replace(cfg, slippage_bps=0.0), o, ['topk'])
b, s = base.metrics.loc['topk', 'oos_fees_usd'], stress0.metrics.loc['topk', 'oos_fees_usd']
print(('DEFECT 2' if s < b else 'OK 2') + f': base fees {b:.2f} vs "+0 bps stress" fees {s:.2f}')

# 3. synthetic_panel with more than 6 symbols (needed for N>6 scaling instances).
try:
    synthetic_panel(start='2026-09-01', end='2026-09-03', symbols=tuple('ABCDEFGH'))
    print('OK 3')
except Exception as e:
    print('DEFECT 3: synthetic_panel(8 symbols) ->', type(e).__name__, e)

# 4. Default capital vs spec section 4 ($25,000).
print(('OK 4' if ExecutionConfig().starting_capital == 25_000 else 'DEFECT 4') +
      f': default starting_capital={ExecutionConfig().starting_capital}')

# 5. Is there any holdings/cash/fill ledger in the result?
print('DEFECT 5: no fills/holdings ledger' if not hasattr(base, 'fills') else 'OK 5')
