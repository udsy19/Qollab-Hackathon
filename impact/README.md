# QC-TRADE Intraday v2.1 — Alpaca Paper + authenticated historical data

> **Status 2026-10-10 (hackathon build).** Real Alpaca SIP data, 2026 out of sample, after costs: **not profitable and significantly worse than session-flat SPY**; classical solvers matched or beat QAOA on every instance measured. Full results: `docs/impact/FINAL_RESEARCH_REPORT.md` and `docs/impact/BENCHMARK_RESULTS.md` (repo root). Pre-registration: `PREREGISTRATION_2026-10-10.md`. Audit: `AUDIT.md`. The real-data download is `bash scripts/fetch_real_data.sh smoke|pilot|full` (read-only; no orders).

**A reproducible US stocks/ETFs intraday research prototype for net-of-cost out-of-sample alpha testing and quantum-inspired vs classical combinatorial optimization.**

**Status:** The offline test suite passes, and a synthetic end-to-end smoke test has been run. **There are NO independently verified real-data trading results in this delivered archive.** The runtime cannot fetch external licensed minute bars without credentials/network access. The included downloader lets you evaluate real, timestamped historical data on your own machine. Any synthetic metrics are labeled **NON-EVIDENCE**. The program NEVER sends broker orders.


## NEW: Alpaca Paper Account integration (read-only)

This project supports your Alpaca **paper** account to authenticate against
Alpaca's **official** trading and market data endpoints, then download real
historical SIP minute bars, backtest them, benchmark QUBO and QAOA, and produce
a conservative OOS evidence audit.

**It cannot place any orders:** `check-alpaca` and `fetch-alpaca` use GET requests
only, and there is no broker order-posting function anywhere in the project.
The paper trading base `https://paper-api.alpaca.markets/v2` is **not** the data
base: historical prices come from `https://data.alpaca.markets/v2`.

**Protect your keys:** If you shared your Alpaca secret in a chat, revoke and
regenerate it in Alpaca. Never paste the replacement into the chat or commit it
to source. The runner asks for rotated keys with terminal echo disabled and
keeps them in the process environment only, not in a `.env` file.

```bash
cd QC_TRADE_Alpaca_Paper_v21
python -m pip install -r requirements.txt
python -m pytest -q

# One command to securely prompt for paper API credentials, check READ-ONLY
# connectivity, download historical SIP bars, and perform a pilot OOS study.
bash scripts/run_research.sh pilot

# After validating data coverage/quality, a multi-year locked 2026 holdout.
# Pre-register choices on 2024/2025 before inspecting 2026 returns.
bash scripts/run_research.sh full
```

If you're already using environment variables, the runner detects them and
doesn't prompt. It never prints or serializes them. Results appear under
`outputs/real_pilot_*` or `outputs/real_full_*` with `RESEARCH_AUDIT.md`,
`research_audit.json`, a plot, solver results, order logs, provenance, and
transaction-cost stress comparisons. **Real profits are NOT established by this
archive**: external Alpaca network access is unavailable in the author's
sandbox, so only mocked integration tests and synthetic demonstrations were run.

A credential/API access test can also be run separately:

```bash
# First export keys locally, or run the secure interactive script above.
python -m qc_trade.cli check-alpaca --feed sip
```

A smaller IEX-only study can be requested by substituting `--feed iex` in
`fetch-alpaca`, but do **not** mix IEX live data with SIP backtest results and
assume the signal behavior or fill costs transfer. For a realistic forward
paper trade, use a consistent live feed and measure actual simulated order
submissions and confirmations *after explicit authorization*.

**Read-only functionality delivered here:**

- GET `/v2/account` on paper endpoint to confirm paper-account credentials;
  prints only status/booleans, no account IDs, balances or secrets
- GET `/v2/clock` on paper endpoint to check the market clock
- GET `/v2/stocks/bars` on data endpoint to check historical SPY bars
- Authenticated, paginated historical data download with atomic complete-file
  publication; interrupted sessions leave only a `.partial` file
- OOS audit with sample-size, excess-over-intraday-SPY, bootstrap interval,
  cost-stress and no-quantum-advantage diagnostics

Review `ALPACA_PAPER_RUNBOOK.md` for troubleshooting and the distinction
between paper execution and historical data simulation.

---

## Start here

```bash
cd QC_TRADE_Intraday_v2
python -m pip install -r requirements.txt
python -m pytest -q
```

### A: Free genuine historical intraday data (no API keys)

A third-party data vendor provides a **free, real July–December 2022 minute-bar sample** with SPY, KO, TSLA, and TWTR. The code downloads from the provider's publicly linked archive, reads raw OHLCV, and *does not redistribute vendor data*. This is a small selected universe with ~one-quarter OOS; use it for plumbing validation, **not** a robust alpha claim. Requires a local internet connection. The provider may change the archive path or terms.

```bash
python -m qc_trade.cli fetch-public-sample \
  --out data/public_sample_2022.csv

# Avoid TWTR delisting in the first profitability experiment; use three survivor
# tickers, split 2022H2 chronologically; small/unrepresentative by design.
python -m qc_trade.cli backtest \
  --data data/public_sample_2022.csv \
  --symbols SPY,KO,TSLA \
  --test-start 2022-10-03 \
  --k 2 --benchmark --snapshots 8 --stress \
  --out outputs/public_sample_research
```

Public historical sample source: https://historicaldata.net/stocks.html (link to sample archive under "CSV File Format & Free Sample Download"). As of Oct 2026 the direct URL is `https://historicaldata.net/file/stocks_sample_2022H2.zip`. **We haven't executed this download against its live endpoint inside the sandbox.** If the provider changes its ZIP structure or download URL, use the Alpaca flow below. The sample has adjustment/corporate-action fields; the model uses **RAW** prices and does not hold overnight.

### B: Real SPY/QQQ/IWM/DIA/TLT/GLD historical data from Alpaca

Sign up for your own free market-data-capable Alpaca account and keep the credentials in your **shell environment**, not in the repository. For old historical SIP bars, Alpaca Basic generally permits access as long as the query end is **at least 15 minutes in the past**. The free live IEX feed covers only the IEX exchange; this research uses **historical SIP** where allowed for better representation of US consolidated executions. Verify Alpaca's current entitlement terms.

```bash
export APCA_API_KEY_ID='YOUR_PERSONAL_KEY'
export APCA_API_SECRET_KEY='YOUR_PERSONAL_SECRET'

# Start date is UTC-inclusive; end boundary is UTC; Alpaca defines its exact timestamp as inclusive, but midnight of 2026-10-10 lies after the Oct 9 regular session.
# Historical data: development 2024, validation 2025, locked holdout in 2026.
python -m qc_trade.cli fetch-alpaca \
  --symbols SPY,QQQ,IWM,DIA,TLT,GLD \
  --start 2024-01-01 --end 2026-10-10 \
  --feed sip --out data/us_etfs_1min.csv

python -m qc_trade.cli backtest \
  --data data/us_etfs_1min.csv \
  --symbols SPY,QQQ,IWM,DIA,TLT,GLD \
  --test-start 2026-01-02 \
  --k 2 --history-bars 312 \
  --rebalance-minutes 30 \
  --execution-lag-bars 2 \
  --benchmark --sizes 4,6 \
  --snapshots 12 --benchmark-repeats 5 \
  --stress --stress-bps 0,1.5,5,10 \
  --out outputs/etfs_2026_oos
```

The request may take a while (~millions of 1m records across multiple years); the API downloader writes each page directly to disk instead of storing all pages in memory. The current CSV loading and calendar-aggregation stage **does** use memory; plan for ample RAM or split into smaller, separately evaluated historical periods. The app does **not** retrieve API credentials from a broker account automatically.

**If session validation fails:** inspect the exception, JSON diagnostics, the source feed, symbol liquidity, holidays, partial days, and missing minute buckets. `--min-minute-bars 4` accepts 4 of 5 minute observations per 5-minute bar **but reduces quality**; changing thresholds to make results look profitable is data snooping. Defaults require all five constituent minutes and reject a backtest if >15% of exchange sessions are missing.

### C: Synthetic mechanics smoke test, not investing research

```bash
python -m qc_trade.cli demo \
  --history-bars 80 --anneal-steps 70 --anneal-restarts 2 \
  --benchmark --snapshots 2 --benchmark-repeats 2 \
  --qaoa-maxiter 35 --qaoa-shots 256 \
  --stress --out outputs/demo
```

The included `outputs/demo_v2/` were generated from **synthetic, randomized data** and are meant to demonstrate file formats and check pipeline mechanics, not estimate actual market performance. Rerun experiments on authenticated real data before drawing investment conclusions.

## Source paper and mathematical adaptation

Paper: Shinde et al., *A quantum computing approach to beam angle optimization* (2025), https://arxiv.org/pdf/2504.07844 . Its method coordinates **binary beam selection** with **continuous spot-intensity refinement** using ICR/ADMM; the "quantum" part was a simulated classical MATLAB QUBO solver, not real quantum hardware. Our adaptation retains the **mixed discrete/continuous structure**, but DOES NOT claim to reproduce its full ADMM/ICR updates.

We choose exactly `K` equities for the next intraday holding window by optimizing a binary support proposal `y_i∈{0,1}` via equal-weight capital proxy `w_i=y_i/K`:

\[
E(y)=-\frac{\mu^\top y}{K}+\frac{\gamma}{2K^2}y^\top\Sigma y + c\lVert y/K-w_{t-1}\rVert_1,
\qquad \mathbf1^\top y=K.
\]

The L1 turnover term is **EXACTLY linear in each binary `y_i` when the prior weights are fixed**; the constant `c ||w_prev||_1` is dropped from the QUBO matrix without changing the argmin. The `K`-hot constraint is enforced natively by the enumeration, swap-annealing, and HiGHS MILP solvers. The X-mixer QAOA uses a quadratic cardinality penalty plus feasible-shot post-selection; the XY-mixer QAOA starts in a uniform K-hot superposition and preserves Hamming weight by construction.

Then we re-optimize weights on the selected support, subject to `sum(w)=1`, min/max selected weight limits, long-only positions, and the original mean-risk-turnover objective:

\[
\min_w\; -\mu^\top w + \frac{\gamma}{2}w^\top\Sigma w + c\lVert w-w_{t-1}\rVert_1,
\qquad\sum_iw_i=1,\quad 0\le w_i\le u y_i,\quad w_i\ge \ell y_i.
\]

The step-1 QUBO **only optimizes an equal-weight proxy**, not the full original continuous-weight problem. All-support enumeration plus continuous sizing is the stronger global reference at small sizes. SLSQP uses smoothed L1 to solve the convex fixed-support problem numerically. Minor numerical errors are possible; feasibility is tested.

### Trading signals are NOT a quantum advantage

For each decision after the 5-minute bar completes, estimate **next 30-minute holding horizon** mean returns from trailing 6-bar and 30-bar momentum, with fixed shrinkage. Covariance uses strictly historical **within-day close-to-close returns only**, shrunk 25% toward diagonal. Forecasting is intentionally rudimentary. Quantum-inspired optimization does not create predictive trading signals.

## Execution realism and timing

1. Market hours are determined from `XNYS` exchange calendar, including US time zone/DST and half-days.
2. Raw source **1-minute start-time buckets** are aggregated into complete 5-minute OHLCV buckets. No missing observations are filled, and no returns are computed across adjacent sessions for forecasts.
3. A 09:55–10:00 bar closes at **10:00**; its completed close/volume becomes available at 10:00.
4. Default `--execution-lag-bars 2` fills at the 10:05 5-minute bar **open** (a deliberately conservative 5-minute wait after the earliest same-boundary fill). More lag can be stress-tested.
5. The model marks pre-fill holdings from prior close to the execution open, executes the target weight at the open less estimated costs, then marks from that open to bar close.
6. The system forces all positions flat **at the START of the final 5-minute session bucket** (e.g. 15:55 normal session), never at an assumed executable 16:00 closing print. NYSE early closes handled.
7. Executed turnover is `sum(abs(target - drifted_weights))`, i.e. buys **plus** sells. Cost fraction of NAV is each leg's notional share times full-spread/2 + fixed slippage + commission + nonlinear impact, as configured. This is not order-book replay or measured historical fill prices.
8. A new order exceeding the configured % of preceding **observed** 5-minute dollar volume is rejected. Forced liquidation bypasses that guard for safety and records the estimated participation.
9. Assumes cash earns 0%, no leverage, no shorts, no borrow fees, no dividend credit (flat overnight), no tax, no partial fills or halts within a completed 5-minute bar.
10. Time-indexed OHLCV bars cannot prove executable real-world fill prices. For serious research, add historical quotes/NBBO, trades, venue routing, order-queue simulation, and broker paper trading.

## In-sample / holdout protocol

- **Development:** use 2024. Set candidate universe, optimizer settings, costs, signal family, and data filters.
- **Validation:** use 2025, rolling walk-forward fitting of the signals on *only prior* bars; tune strategies using precommitted validation procedures and freeze the configuration.
- **Locked out-of-sample:** evaluate 2026 **once** with `--test-start 2026-01-02`. Signal fitting in 2026 still uses only trailing observations, while all hyperparameters remain fixed from earlier years.
- **Before publication:** repeat on another precommitted market period/universe and walk through trade logs, data completeness, adjustments, and fills.

This software enforces **chronological signal formation and an explicit holdout start** but **does not automate nested CV/hyperparameter selection or prevent a person from repeatedly tuning on the 2026 test**. Do not claim that such manual retuning is an untouched OOS test. A frozen static ETF universe chosen ex post still contains selection bias; ETFs here were chosen as common liquid examples, not a survivorship-free dynamic universe.

## Classical/quantum computational benchmarks

`--benchmark` gathers identical historical decision snapshots with fixed `mu`, `cov`, and `previous_weights` for every method. Each snapshot has *two* prior-holdings scenarios: flat and invested. Complexity grid: selected N values (`--sizes 4,6,8`, larger sizes for classical-only if you have more symbols). Results include:

| Method | Interpretation |
| --- | --- |
| `exact_qubo` | Globally exact K-subset enumeration of the QUBO, when tractable |
| `milp_qubo` | Strong classical **HiGHS MILP** QUBO solver: binary-linear McCormick constraints plus RLT cuts; records the certified MIP gap, and a time-out without a gap as uncertified |
| `greedy` | Classical greedy swap local search |
| `anneal` | Classical K-hot multi-restart stochastic annealing |
| `topk` | Simple highest predicted return assets |
| `full_exact` | Enumerate all supports then solve weights for each; global discrete+continuous reference for small N |
| `qaoa` | **Qiskit** QAOA, **X mixer** with the provably minimal K-hot penalty; simulated with qiskit-aer; decodes the feasible shot with the lowest true energy |
| `qaoa_xy` | **Qiskit** QAOA, **K-preserving XY ring mixer** from a Dicke state; simulated with qiskit-aer |
| `random_khot` | Control: uniform random K-hot samples with the same shot budget as QAOA (judge QAOA against this, not just against "found the optimum") |

The `qaoa`/`qaoa_xy` methods build **Qiskit** circuits (`qc_trade/qaoa.py`) and simulate them with **qiskit-aer on a classical processor**, not on quantum hardware; a NumPy statevector survives only as the test oracle. Total measured time includes building Q, classical variational optimization, statevector evolution, sampling and continuous weight refinement. Missing hardware overhead (transpilation, Dicke-state preparation, queueing, calibration, noisy shots) means **no hardware advantage is demonstrated**. Unlike the original paper, this v2 uses both exact and MILP classical comparators; these can readily outperform statevector simulations at small K.

Compare: K-hot feasibility %, difference from exact QUBO energy, difference from globally best refined portfolio objective (small N), runtime distribution across fixed seeds, QAOA feasible-shot fraction, parameter evaluations, and scaling as N grows. QUBO gaps close to zero establish **optimization accuracy**, not investment profitability. An end-to-end quantum speedup claim would additionally require real-hardware runtime and suitable classical compute parity.

## Profitability baselines and research outputs

- `spy`: SPY **intraday-only** exposure matching the strategy's entry window and nightly liquidation; not passive 24h SPY buy-and-hold.
- `equal`: equal-weight all candidate assets, same intraday timing and execution costs.
- `cash`: cash (zero return and zero fees).
- `topk`: top K forecast returns with continuous refinement.
- `minvar`: low individual-volatility K assets, continuously optimized.
- `greedy`, `anneal`, `exact_qubo`, `milp_qubo`: same forecast and portfolio objective, different support solvers.
- `full_exact`, `qaoa` and `qaoa_xy` can be used as backtest methods, but are expensive and intended mostly for sampled optimization benchmarks.

`outputs/<experiment>/` contains:

| File | Meaning |
| --- | --- |
| `metrics_oos.csv` | **TEST ONLY** net return, annualized return, Sharpe (0 risk-free), max daily drawdown, win-day fraction, trades, fees, optimizer runtime |
| `daily_oos_returns.csv` | Daily portfolio OOS returns used in bootstrap and risk calculations |
| `orders.csv` | Explicit delayed fills, forced flats, size, liquidity participation, cost |
| `forecasts.csv` | Forecast timestamps, fill timestamps, trailing observed return counts |
| `bar_equity.csv` | Net-of-cost bar-level equity for every tested strategy |
| `oos_equity.png` | Out-of-sample equity visualization |
| `paired_bootstrap_vs_spy.csv` | Descriptive 5-day circular-block bootstrap of paired mean daily excess bps vs session-matched SPY; NaN under 30 OOS days |
| `solver_benchmark_trials.csv` | Every solver attempt on frozen snapshot including seed/gaps/time/quantum feasible mass |
| `solver_benchmark_summary.csv` | Grouped benchmark summary by size and solver |
| `cost_stress_grid.csv` | Optional repeated holdouts varying extra fill slippage, without retuning expected optimizer cost |
| `manifest.json` | Source data SHA256, exact rules/assumptions and run configuration |

**Cost stress:** `--stress --stress-bps 0,1.5,5,10` changes per-traded-dollar **additional slippage per side**, while keeping spread/impact/commission and all optimization hyperparameters fixed. A profitable result at zero cost which disappears at 5bp is **not** strong evidence for a tradeable edge.

**Research success thresholds to pre-register:** positive net OOS return after realistic costs and cash, positive excess versus session-matched SPY and top-K with cost sensitivity, paired excess-return uncertainty intervals preferably above zero on sufficiently large samples, stable drawdowns/trading activity, and independent chronological replications. For computational advantage, QAOA should beat or competitively match certified HiGHS and exact discrete+continuous classical methods on the **same** instances within genuinely comparable resource budgets. No result currently meets these thresholds, because no live market-data backtest was performed in this environment.

## Requirements, tests, code paths

- Python 3.10+; tested in this environment on Python 3.13.
- `qc_trade/data.py`: licensed minute data ingestion, timezone normalization, XNYS calendar, missing-bar gating, provenance.
- `qc_trade/backtest.py`: strict information times, forecasts, execution, mark-to-market, costs, bootstraps.
- `qc_trade/optimizer.py`: QUBO, exact search, HiGHS MILP, annealing, greedy, ideal QAOA X and XY, SLSQP.
- `qc_trade/benchmark.py`: frozen-input solver comparisons.
- `qc_trade/cli.py`: reproducible commands, CSV/PNG/JSON artifacts.
- `qc_trade/demo.py`: synthetic fixture generator (explicitly NOT REAL market data).
- `tests/test_intraday.py`: leakage, date/calendar, constraints, numerical classical optimality and QAOA validity tests.

## What to implement after the first genuine OOS run

1. Acquire and verify bid/ask quotes and eligible consolidated trades, audit 1-minute data timestamps, corporate events, missing intervals, ETF histories, and delisted securities where relevant.
2. Replace the weak momentum forecast with pre-registered out-of-sample competing return models (ridge, boosted trees, volatility-conditioned regressions), purged CV, and calibration; isolate the forecast contribution from optimizer contribution.
3. Improve liquidity/price execution: bid/ask quote replay, lot sizes, market/limit order policies, adverse selection, order latency and queue position.
4. Implement a mixed-binary-continuous solver (commercial MIQP or SCIP, licensed where needed) as a proper **end-to-end** global benchmark for larger portfolios rather than only the equal-weight QUBO.
5. Extend cardinality constraints with sectors, factor exposures, risk budget, CVaR, confidence regions for forecasts, dynamic position caps and event blackouts.
6. Use genuine Qiskit Aer and IBM/other accessible QPUs **after** statistical alpha survives simple classical methods; count circuit transpilation, Dicke-state preparation, shots, calibration, queue delay, optimizer iterations, noise and failure probability.
7. Deploy to sandbox/paper-trading with immutable signals and order audit; move to live trading only after passing separate risk and regulatory reviews.

## References

- Original study: https://arxiv.org/pdf/2504.07844
- Alpaca feed coverage / entitlement: https://docs.alpaca.markets/us/docs/about-market-data-api
- Alpaca historical SIP 15-minute limitation: https://docs.alpaca.markets/us/docs/market-data-faq
- Public vendor sample: https://historicaldata.net/stocks.html
- NYSE trading calendar: https://www.nyse.com/markets/hours-calendars

**This is experimental research software, not investment advice or a live trading application. Trading can lose money. Historical backtests do not guarantee real-world execution or future returns.**
