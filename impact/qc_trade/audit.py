"""Pre-committed intraday research evidence report.

This audit is conservative: every diagnostic is descriptive, not proof of
future profitability or quantum computational advantage. No broker orders.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd


def audit_results(out: Path, *, method: str = 'milp_qubo') -> dict:
    out = Path(out)
    manifest = json.loads((out / 'manifest.json').read_text())
    results = pd.read_csv(out / 'metrics_oos.csv').set_index('method')
    if method not in results.index or 'spy' not in results.index:
        raise ValueError('Audited strategy and SPY comparator must be in results')
    target = results.loc[method]
    ref = results.loc['spy']
    sample_days = int(target.oos_sessions)
    alpha = float(target.oos_total_return - ref.oos_total_return)
    boots = pd.read_csv(out / 'paired_bootstrap_vs_spy.csv')
    selected = boots[boots.method == method]
    ci_lower = float(selected.bootstrap_ci_low_bps.iloc[0]) if len(selected) else np.nan
    ci_upper = float(selected.bootstrap_ci_high_bps.iloc[0]) if len(selected) else np.nan
    stressed = pd.read_csv(out / 'cost_stress_grid.csv')
    row = stressed[(stressed.method == method) & (np.isclose(stressed.slippage_bps_per_side,5))]
    stressed_return = float(row.oos_total_return.iloc[0]) if len(row) else np.nan
    benchmark = pd.read_csv(out / 'solver_benchmark_summary.csv')
    c = benchmark[(benchmark.method == 'milp_qubo') & (benchmark.n == benchmark.n.max())]
    q = benchmark[(benchmark.method == 'qaoa_xy') & (benchmark.n == benchmark.n.max())]
    valid_sample = sample_days >= 60
    gates = {
        'genuine_historical_input': not bool(manifest.get('synthetic_data',True)),
        'at_least_60_oos_sessions': valid_sample,
        'positive_oos_net_return': bool(target.oos_total_return > 0),
        'higher_net_return_than_intraday_spy_baseline': bool(alpha > 0),
        'paired_bootstrap_95pct_lower_above_zero_bps_per_day': bool(np.isfinite(ci_lower) and ci_lower > 0),
        'positive_return_with_5bps_slippage_per_side': bool(np.isfinite(stressed_return) and stressed_return > 0),
    }
    report = {
        'method': method,
        'synthetic_data': bool(manifest.get('synthetic_data',True)),
        'data_source': manifest.get('data_source'),
        'oos_sessions': sample_days,
        'strategy_oos_total_return': float(target.oos_total_return),
        'spy_intraday_oos_total_return': float(ref.oos_total_return),
        'arithmetic_total_return_difference': alpha,
        'strategy_oos_sharpe_zero_rf': float(target.oos_sharpe_rf0),
        'strategy_oos_max_drawdown': float(target.oos_max_drawdown),
        'strategy_oos_trading_cost_usd': float(target.oos_fees_usd),
        'paired_daily_excess_bootstrap_ci95_bps': [ci_lower, ci_upper],
        'strategy_net_return_at_5bps_slippage_per_side': stressed_return,
        'milp_median_solver_seconds_largest_n': float(c.median_seconds.iloc[0]) if len(c) else None,
        'xy_qaoa_statevector_median_seconds_largest_n': float(q.median_seconds.iloc[0]) if len(q) else None,
        'gates': gates,
        'all_gates_passed': all(gates.values()),
        'quantum_advantage_established': False,
        'paper_order_authorized': False,
        'limitations': [
            'OOS holdout should be genuinely locked before hyperparameter and universe selection.',
            'A single backtest, even if positive, does not predict future returns.',
            'Cost assumptions are modeled; quote-level slippage and paper-to-real fills differ.',
            'Bootstrap confidence intervals are exploratory; repeated strategy selection is multiple testing.',
            'QAOA is ideal classical statevector simulation, NOT quantum hardware speedup.',
            'No paper or live orders were placed.',
        ],
    }
    (out / 'research_audit.json').write_text(json.dumps(report, indent=2, allow_nan=True))
    def pct(x):
        return f'{x*100:+.2f}%' if np.isfinite(x) else 'n/a'
    def flag(x):
        return 'PASS' if x else 'FAIL / UNPROVEN'
    text = [
        '# QC-TRADE Intraday OOS Audit',
        '',
        '> This is a synthetic software demonstration, NOT genuine trading evidence.'
        if report['synthetic_data'] else '> Actual historical bars; retrospective simulated executions, not real broker fills.',
        '',
        f'- Strategy: `{method}`',
        f'- OOS NYSE sessions: {sample_days}',
        f'- Strategy net return: {pct(float(target.oos_total_return))}',
        f'- Session-matched intraday SPY net return: {pct(float(ref.oos_total_return))}',
        f'- Arithmetic total return difference: {pct(alpha)}',
        f'- Strategy max drawdown: {pct(float(target.oos_max_drawdown))}',
        f'- 5 bps per-side stress net return: {pct(stressed_return)}',
        f'- Exploratory paired mean daily excess 95% bootstrap interval (bps): [{ci_lower:.2f}, {ci_upper:.2f}]',
        '', '## Prespecified evidence gates', '',
    ]
    text += [f'- {flag(success)}: {gate.replace("_"," ")}' for gate,success in gates.items()]
    text += ['', '## Important limitations', '']
    text += [f'- {limitation}' for limitation in report['limitations']]
    text += ['', '**No quantum advantage or future profitability has been established.**', '']
    (out / 'RESEARCH_AUDIT.md').write_text('\n'.join(text))
    return report
