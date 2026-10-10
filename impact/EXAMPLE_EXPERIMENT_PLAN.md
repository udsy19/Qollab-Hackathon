# Example locked US ETF intraday experiment — registration template

Use this document to record the pre-holdout decision in a version-control commit. It is NOT evidence that results have already been obtained.

## Research hypothesis

At 5-minute signal/30-minute reallocation cadence, a hybrid binary-selection + continuous-sizing portfolio strategy produces **higher net-of-cost average daily out-of-sample returns** and **lower drawdown**, at equivalent market exposure, than simple top-K momentum and a session-flat SPY baseline. The candidate quantum solver, separately, improves the discrete objective quality or time-to-target over certified classical MILP for the same QUBO inputs on feasible problem sizes.

Hypothesis is falsifiable. A result that returns less than cash or a classical baseline invalidates the trading claim. A QAOA simulator that takes more time than a MILP and finds no better objective invalidates an algorithmic speed claim for that experiment.

## Preliminary specification

| Dimension | Frozen choice |
| --- | --- |
| Universe | SPY, QQQ, IWM, DIA, TLT, GLD (ETF candidates, known before sample) |
| Training/development | 2024-01-02–2024-12-31 |
| Validation | 2025-01-02–2025-12-31 |
| Locked OOS | 2026-01-02–2026-10-09 (later periods for replication) |
| Data | Official Alpaca historical consolidated SIP 1m OHLCV if entitled |
| Intraday decision | 5-minute completed candle signals |
| Rebalance | Every 30 minutes from 10 AM NY time |
| Delay | 5-minute wait after end of observed signal bar, fill at next subsequent 5m bucket open |
| Sizing | Full investment in exactly K=2 long positions during holding period |
| Prior | No overnight holdings; forced exit at first instant of final 5m bar |
| QUBO | Cardinality-constrained equal-weight proxy plus expected turnover costs |
| Risk/alpha | Fixed trailing returns, momentum shrinkage, diagonal-shrunk covariance |
| Candidate solvers | Exhaustive, MILP, greedy, annealing, ideal QAOA X, ideal QAOA XY |
| Cost stress | Per-side additional slippage 0, 1.5, 5, 10 bps + baseline spread/commission/impact |
| Test statistics | Net OOS daily returns, 5day block-bootstrap paired excess mean vs SPY, drawdown, turnover, liquidity |

## Gaps that must be addressed to claim tradeable profitability

* Quote-based bid/ask spreads are more credible than flat assumed spread; currently these are hypothetical friction inputs.
* Large-model and frequent-hypothesis overfitting; this program fixes parameters when requested but does not prevent hindsight changes.
* Approximate bar-open fills assume adequate liquidity exactly when markets print; a proper exchange execution simulator is a future feature.
* No overnight exposure can make performance very different from passive ETF index investment. Session-flat SPY is a fairer comparator for that exposure; passive total-return SPY also deserves a separate comparison.
* Two-to-nine-asset test cases cannot demonstrate an asymptotic quantum advantage over excellent MILP solvers.
* Real economic edge should persist across regimes, reasonable trade volumes, transaction cost estimates, and untouched replication cohorts.

## Recording results

Attach raw input SHA256, manifest JSON, unmodified `metrics_oos.csv`, `paired_bootstrap_vs_spy.csv`, `cost_stress_grid.csv`, `solver_benchmark_trials.csv`, and the complete `orders.csv`. Do not drop losing methods or failed solver seeds. Keep data/source entitlements, runtime environment, and any portfolio construction exceptions in a supplementary note.
