"""Old weight-drift engine vs new share/cash ledger, identical settings.
argv[1] = path whose qc_trade is imported. Prints per-method OOS return, fees, trades as JSON."""
import sys, json
sys.path.insert(0, sys.argv[1])
from dataclasses import replace, fields
from qc_trade.demo import synthetic_panel
from qc_trade.optimizer import OptConfig
from qc_trade.backtest import ExecutionConfig, run_backtest
p = synthetic_panel()
kw = dict(test_start='2026-09-14', history_bars=80, starting_capital=float(sys.argv[3]) if len(sys.argv) > 3 else 100_000)
if 'whole_shares' in {f.name for f in fields(ExecutionConfig)}:
    kw['whole_shares'] = sys.argv[2] == 'whole'
e = ExecutionConfig(**kw)
o = OptConfig(k=2, anneal_steps=70, anneal_restarts=2)
r = run_backtest(p, e, o, ['topk', 'spy', 'equal', 'milp_qubo', 'minvar'])
print(json.dumps({m: [round(float(r.metrics.loc[m, 'oos_total_return']), 6), round(float(r.metrics.loc[m, 'oos_fees_usd']), 2),
                      int(r.metrics.loc[m, 'oos_trades'])] for m in r.metrics.index}))
