# QC-TRADE Intraday OOS Audit

> This is a synthetic software demonstration, NOT genuine trading evidence.

- Strategy: `milp_qubo`
- OOS NYSE sessions: 10
- Strategy net return: -2.50%
- Session-matched intraday SPY net return: -1.36%
- Arithmetic total return difference: -1.15%
- Strategy max drawdown: -4.13%
- Net return with 5 bps EXTRA slippage per side: -6.50%
- Net return by modeled cost scenario: optimistic -1.14%, base -2.50%, conservative -4.73%, severe_stress -12.52%
- Exploratory paired mean daily excess 95% bootstrap interval (bps): [nan, nan]

## Prespecified evidence gates

- FAIL / UNPROVEN: genuine historical input
- FAIL / UNPROVEN: at least 60 oos sessions
- FAIL / UNPROVEN: positive oos net return
- FAIL / UNPROVEN: higher net return than intraday spy baseline
- FAIL / UNPROVEN: paired bootstrap 95pct lower above zero bps per day
- FAIL / UNPROVEN: positive return with 5bps extra slippage per side
- FAIL / UNPROVEN: positive oos net return conservative costs

## Important limitations

- OOS holdout should be genuinely locked before hyperparameter and universe selection.
- A single backtest, even if positive, does not predict future returns.
- Spread, slippage, impact and fill assumptions are MODELED from OHLCV bars, not observed quotes; quote-level slippage and paper-to-real fills differ.
- Bootstrap confidence intervals are exploratory; repeated strategy selection is multiple testing.
- QAOA is ideal classical statevector simulation, NOT quantum hardware speedup.
- No paper or live orders were placed.

**No quantum advantage or future profitability has been established.**
