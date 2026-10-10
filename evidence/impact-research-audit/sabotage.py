"""Sabotage round on a DISPOSABLE copy of impact/. argv[1]=source impact dir, argv[2]=scratch dir.
Each sabotage: fresh copy, one textual mutation (must match exactly once), run named tests.
A sabotage whose tests stay GREEN is a NULL result: the gate cannot see that defect."""
import shutil, subprocess, sys, pathlib
SRC, SCR = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
PY = '/tmp/qct-venv/bin/python'
T = 'tests/test_backtest_integrity.py'
OLD = 'tests/test_intraday.py::test_future_bar_alteration_does_not_change_old_orders'
SAB = [
 ('S1 forecast peeks one bar ahead (look-ahead)', 'qc_trade/backtest.py',
  'R = cache[pos-e.history_bars:pos]', 'R = cache[pos-e.history_bars+1:pos+1]',
  [T + '::test_future_price_perturbation_does_not_change_past']),
 ('S2 participation uses the fill bar\'s OWN volume/close (same-bar peek)', 'qc_trade/backtest.py',
  'A_volume[t-1], A_close[t-1], e, forced=forced)', 'A_volume[t], A_close[t], e, forced=forced)',
  [T + '::test_future_price_perturbation_does_not_change_past', T + '::test_fill_at_a_bar_open_uses_nothing_from_that_bar_but_its_open']),
 ('S3 fill at the PREVIOUS bar close instead of this bar open', 'qc_trade/backtest.py',
  'ex = _execute(shares[method], cash[method], target, A_open[t],', 'ex = _execute(shares[method], cash[method], target, A_close[t-1],',
  [T + '::test_fills_are_at_a_later_bar_open_never_the_signal_bar']),
 ('S4 commission not debited from cash', 'qc_trade/backtest.py',
  '        cash -= q * price + fee\n', '        cash -= q * price\n',
  [T + '::test_equity_is_cash_plus_holdings_rebuilt_from_fills']),
 ('S5 buys not limited to cash (leverage allowed)', 'qc_trade/backtest.py',
  '    if need > cash:\n', '    if False:\n',
  [T + '::test_equity_is_cash_plus_holdings_rebuilt_from_fills']),
 ('S6 forced end-of-day liquidation disabled AND engine overnight assertion disabled', 'qc_trade/backtest.py',
  "            if last[t]:\n                # The exit", "            if False:\n                # The exit",
  [T + '::test_flat_at_every_session_end_and_liquidation_is_costed']),
 ('S7 contiguity guard removed', 'qc_trade/backtest.py',
  '    validate_panel(panel)\n    times', '    times',
  [T + '::test_noncontiguous_panel_is_refused']),
 ('S8 stress grid replaces slippage instead of adding', 'qc_trade/backtest.py',
  'replace(e, slippage_bps=e.slippage_bps+extra)', 'replace(e, slippage_bps=extra)',
  [T + '::test_zero_extra_stress_equals_base_and_cost_is_additive']),
 ('S9 conservative-cost gate threshold disabled (always True)', 'qc_trade/audit.py',
  "and scenario_return['conservative'] > 0)", "or True)",
  [T + '::test_audit_never_validates_a_strategy_profitable_only_under_optimistic_costs']),
 ('S10 severe scenario cheaper than conservative', 'qc_trade/backtest.py',
  "'severe_stress': {'spread_bps': 5.0, 'slippage_bps': 10.0", "'severe_stress': {'spread_bps': 0.0, 'slippage_bps': 0.0",
  [T + '::test_four_cost_scenarios_are_ordered']),
 ('S11 TEST transform disabled: perturbation is the identity', T,
  '    return BarPanel(o, c, v, panel.days, panel.diagnostics)\n\n\ndef _before',
  '    return panel\n\n\ndef _before',
  [T + '::test_future_price_perturbation_does_not_change_past']),
 ('S12 fractional shares by default', 'qc_trade/backtest.py',
  'whole_shares: bool = True', 'whole_shares: bool = False',
  [T + '::test_whole_shares_by_default']),
]
if len(sys.argv) > 3:
    SAB = [s for s in SAB if s[0].split()[0] in sys.argv[3].split(',')]
# S6 also needs the engine's own overnight assertion off, so the TEST must be the one to catch it
EXTRA = {'S5 buys not limited to cash (leverage allowed)':
         ('qc_trade/backtest.py', "raise RuntimeError('Ledger went negative: buys exceeded available cash')", 'pass'),
         'S6 forced end-of-day liquidation disabled AND engine overnight assertion disabled':
         ('qc_trade/backtest.py', "raise AssertionError('Overnight holdings must be zero')", 'pass')}
for name, rel, old, new, tests in SAB:
    if SCR.exists():
        shutil.rmtree(SCR)
    shutil.copytree(SRC, SCR, ignore=shutil.ignore_patterns('outputs', '__pycache__', '.pytest_cache'))
    muts = [(rel, old, new)] + ([EXTRA[name]] if name in EXTRA else [])
    for r, o, n in muts:
        f = SCR / r
        s = f.read_text()
        assert s.count(o) == 1, f'{name}: mutation anchor matched {s.count(o)} times in {r}'
        f.write_text(s.replace(o, n))
    for test in tests:
        res = subprocess.run([PY, '-m', 'pytest', '-q', '-x', '-p', 'no:cacheprovider', test], cwd=SCR,
                             capture_output=True, text=True)
        last = (res.stdout.strip().splitlines() or ['?'])[-1]
        verdict = 'RED (caught)' if res.returncode != 0 else 'GREEN -> NULL RESULT'
        print(f'{name} | {test.split("::")[-1]} | {verdict} | {last}', flush=True)
shutil.rmtree(SCR, ignore_errors=True)
