# QC-TRADE v2: pre-registration and independent audit

**Purpose:** prevent an optimizer win from being incorrectly interpreted as a quantum advantage or as a profitable intraday strategy.

## Before the holdout is unlocked

- [ ] Fix liquidity universe using historical listing data *as of the development date*; record ticker changes, delistings, ETF launch dates.
- [ ] Commit SHA-256 checksums of raw vendor market data, 1-minute bar start/end convention, exchange feed, source timestamp semantics, adjustment convention.
- [ ] Record total/accepted/missing XNYS sessions and rejected reasons. Reject/inspect days rather than forward-filling.
- [ ] Freeze `test_start`, exact universe, `K`, risk aversion, per-position bounds, rebalance period, lookback, momentum parameters, and all capacity limits.
- [ ] For every hyperparameter, show how it was chosen from *prior* data, and specify model-selection metric and multiple-testing procedure.
- [ ] State that dividends/overnight SPY holding are not compared fairly to an intraday-only strategy without an independently computed total-return benchmark.

## Execution audit

- [ ] For each 10:00 NY signal, verify inputs were only completed bars through 10:00; no 10:05 / 10:10 bar data.
- [ ] Confirm 10:05 fill for 5-minute latency when `execution_lag_bars=2` (signal bar begins 09:55, finishes 10:00).
- [ ] Confirm all portfolios are 100% cash by the *beginning* of final bar on short sessions and normal sessions; no overnight stocks.
- [ ] Confirm a carried portfolio earns close-to-next-open mark-to-market, and a new order gets next open-to-close return only *after* fill.
- [ ] Reconcile spread, slippage, commission and nonlinear price impact assumptions against actual NBBO/venue execution logs before paper-trading claims.
- [ ] Compare 0bp, 1.5bp, 5bp, and 10bp incremental slippage **per traded dollar**; no retuning to test costs.
- [ ] Check order capacity from **prior** 5-minute dollar volume; ensure liquidation diagnostics record cap overrides.

## Optimizer fidelity

- [ ] Publish the same QUBO Q for all methods and confirm integer card `sum(y)=K`.
- [ ] On small N, exhaustive QUBO and certified HiGHS MILP QUBO objective agree to numerical precision.
- [ ] Distinguish K-hot QUBO optimum from actual discrete + weighted global portfolio optimum (`full_exact`).
- [ ] Record each candidate's support, bounded weight feasibility, exact objective and market execution cost separately.
- [ ] For ideal QAOA, record circuit/mixer, number of state amplitudes, shots, COBYLA evaluations, restarts/seeds, feasible probability, wall time.
- [ ] For quantum hardware, include cloud network, queue, transpile, calibration, classical parameter optimizer, measurement and shots in total duration; do not equate ideal simulation with QPU speedup.
- [ ] Do not present a claimed asymptotic runtime advantage from N=4–9 only.

## OOS economics and statistics

- [ ] Use full net-of-cost **out-of-sample** daily equity and per-session returns, and ensure fees are not omitted from first OOS day.
- [ ] Compare to cash, session-flat SPY, equal, top-K, minimum variance, and optimized classical MILP.
- [ ] Compute turnover, net return, annualized return, Sharpe, max drawdown, capacity, percent days with positions and average hold time.
- [ ] Report exploratory 5-day block-bootstrap CI on paired daily return difference vs SPY; no significance claim for small samples.
- [ ] Report per-regime drawdowns/returns and a separate chronology not used for model selection.
- [ ] Correct for the number of variants tested; not every 95% CI >0 establishes a replicated edge.
- [ ] If 2026 is viewed repeatedly, label it validation rather than untouched test and reserve a new final holdout.
- [ ] Never use simulated random-data returns to assert market alpha.

## Publication decision

A positive result requires **two separate proof tracks**: (1) net real-data out-of-sample alpha robust to transaction costs, and (2) quantum end-to-end computational advantage over a strong *classical optimization* baseline. Passing one track does not imply the other. Failure to beat MILP or a simple baseline is a valuable negative result; report it.

## Alpaca Paper/data integration addendum (v2.1)

- [ ] Rotate any API key pair previously disclosed in chat before beginning.
- [ ] Read-only paper account check returns ACTIVE status; credential check must not place orders.
- [ ] Historical SIP data accessible and all six selected ETFs have complete eligible sessions.
- [ ] Market data provenance identifies SIP vs IEX; never silently swap feeds.
- [ ] Use `bash scripts/run_research.sh pilot` for mechanics; do not claim alpha from pilot.
- [ ] Pre-register features/costs and lock 2026 holdout before `bash scripts/run_research.sh full`.
- [ ] Inspect `RESEARCH_AUDIT.md`, not only the strategy's best-looking Sharpe.
- [ ] If any evidence gate fails, do not treat the results as paper-forward-ready.
- [ ] Any later broker order integration requires separate express authorization and explicit risk controls.
