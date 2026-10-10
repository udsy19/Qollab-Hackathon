# QC-TRADE Intraday OOS Audit

> This is a synthetic software demonstration, NOT genuine trading evidence.

- Strategy: `milp_qubo`
- OOS NYSE sessions: 10
- Strategy net return: -1.51%
- Session-matched intraday SPY net return: -1.21%
- Arithmetic total return difference: -0.31%
- Strategy max drawdown: -3.63%
- 5 bps per-side stress net return: -3.48%
- Exploratory paired mean daily excess 95% bootstrap interval (bps): [nan, nan]

## Prespecified evidence gates

- FAIL / UNPROVEN: genuine historical input
- FAIL / UNPROVEN: at least 60 oos sessions
- FAIL / UNPROVEN: positive oos net return
- FAIL / UNPROVEN: higher net return than intraday spy baseline
- FAIL / UNPROVEN: paired bootstrap 95pct lower above zero bps per day
- FAIL / UNPROVEN: positive return with 5bps slippage per side

## Important limitations

- OOS holdout should be genuinely locked before hyperparameter and universe selection.
- A single backtest, even if positive, does not predict future returns.
- Cost assumptions are modeled; quote-level slippage and paper-to-real fills differ.
- Bootstrap confidence intervals are exploratory; repeated strategy selection is multiple testing.
- QAOA is ideal classical statevector simulation, NOT quantum hardware speedup.
- No paper or live orders were placed.

**No quantum advantage or future profitability has been established.**
