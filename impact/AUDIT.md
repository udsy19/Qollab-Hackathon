# QC-TRADE codebase audit (owner spec sections 2 and 6)

Audited 2026-10-10 by agent `research-audit` (Plan row 4), on QC-TRADE v2.1 as imported
(`main` at `0601d77`). Scope: every file in `impact/`. The backtest/execution side was fixed
test-first. Defects in files owned by other agents are recorded here with a proposed fix; they
were not edited.

**Nothing in this audit is market evidence.** Every number below comes from the synthetic
generator in `qc_trade/demo.py` or from random test instances. No network call was made, no
Alpaca key was touched, no order was placed.

## Test results

| tree | command (in `impact/`, venv `/tmp/qct-venv`, Python 3.13.0) | result |
|---|---|---|
| unmodified import | `python -m pytest -q` | `28 passed in 12.68s` (`evidence/impact-research-audit/pytest-before.txt`) |
| new integrity tests on the unmodified tree | `python -m pytest -q tests/test_backtest_integrity.py` | `15 failed in 4.29s` (`evidence/impact-research-audit/integrity-red-before-fix.txt`) |
| after the fixes | `python -m pytest -q` | `43 passed in 8.17s` (`evidence/impact-research-audit/pytest-after.txt`) |

28 + 16 new − 1 superseded = 43.

## What works (checked, not assumed)

- **No look-ahead in the forecasts or the order timing.** Measured on the unmodified engine
  (`evidence/impact-research-audit/probe-leak-unmodified.txt`): independently rescaling open,
  close and volume of every bar after three cut points (mid-session, a session open, late
  session) changed nothing before the cut, for all 9 classical methods. Forecasts at signal bar
  `t` use only within-session close-to-close returns through `close[t]`
  (`backtest.py:closed_bar_returns`, `forecast`). Fills land at `open[t + execution_lag_bars]`,
  10:05 for a 10:00 signal by default.
- **No overnight returns in signals or covariance.** The first bar of each session has a NaN
  return (`closed_bar_returns`, asserted). Positions are flat at every session end.
- **Session-flat SPY baseline.** It enters at the same signal and fill times and is liquidated
  at the same bar, so it does not compare an intraday strategy with an overnight holding.
- **There is no label leakage, because there are no labels.** The forecast is a fixed,
  untrained momentum heuristic (`forecast`), so it has no fitted parameters, no normalisation
  and no train/test split that could be contaminated. This stops being true once spec §4's
  ridge or GBT models land (see N1).
- **Calendar handling.** The XNYS calendar sets the 5-minute grid, early closes and DST
  (`data.py:aggregate_5min`). Incomplete sessions are dropped, never forward-filled.
- **Optimizer parity, as far as the tests reach.** Exact and HiGHS MILP agree on random QUBOs
  up to n=15, and the QUBO equals the equal-weight portfolio objective up to a constant
  (`tests/test_intraday.py`).
- **Read-only Alpaca.** `alpaca_paper.py` issues only `GET`s, allows no redirects and never
  echoes credentials (`tests/test_alpaca_paper.py`).

## Broken, and fixed in this change (test-first; each test went red on the unfixed tree)

| # | defect | where (unmodified tree) | evidence it was real | fix | test |
|---|---|---|---|---|---|
| F1 | **Equity was not derived from holdings, cash and fills.** NAV was a weight-drift product `nav *= 1 + w·(rel − 1)`, with fees as a NAV haircut: no share quantities, no cash balance, no fill log, no whole shares. Spec §6 requires equity "from actual simulated holdings, cash, and fills". | `backtest.py:104-126` (`_fill_cost`, `_drift`), loop `212-264` | `probe-defects-unmodified.txt`: "DEFECT 5: no fills/holdings ledger" | An explicit share/cash ledger (`_execute`). Each order becomes per-leg fills at the bar **open** (sells first, then buys capped to available cash), with integer shares by default. Equity at every bar is `cash + shares·close`. New `fills.csv` and `decisions.csv`. Cross-check: in fractional mode the ledger reproduces the old engine within 1e-5 on every method (`compare_engines.py`; old `topk` −0.021104, new −0.021094), so the old arithmetic was right and only its representation was missing. | `test_equity_is_cash_plus_holdings_rebuilt_from_fills` re-derives NAV from the fill log and market closes, never from the engine's NAV |
| F2 | **The `--stress` grid replaced slippage instead of adding to it.** The README says "additional slippage per side". `cli.py` did `replace(exec_cfg, slippage_bps=slip)`, so the "+0 bps" row was cheaper than the headline run, and the audit's "5 bps" gate meant 5 bps total, not base + 5. | `cli.py:73` | `probe-defects-unmodified.txt`: base fees 1574.00 vs "+0 bps stress" fees 830.45 | `backtest.cost_stress_grid` adds the extra slippage to the base config (`extra_slippage_bps_per_side`, `slippage_bps_total`) | `test_zero_extra_stress_equals_base_and_cost_is_additive` |
| F3 | **No named execution-cost scenarios** (spec §6: optimistic, base, conservative, severe stress). | absent | test red | `COST_SCENARIOS` (`backtest.py:50`) plus `run_cost_scenarios`, which writes `cost_scenarios.csv` under `--stress`. Only frictions vary between scenarios: timing, signals and optimizer settings stay identical. Every row is labelled "MODELED from OHLCV, not observed quotes". | `test_four_cost_scenarios_are_ordered` |
| F4 | **The audit could validate a strategy that was profitable only under optimistic costs** (spec §8). | `audit.py:35-42` | test red: every gate passed with a negative conservative-cost return | New gate `positive_oos_net_return_conservative_costs`. A missing `cost_scenarios.csv` is now a failure (`FileNotFoundError`), not a skip. The severe-stress return is reported. | `test_audit_never_validates_…`, `test_audit_passes_cost_gate_only_when_…`, `test_audit_missing_cost_scenarios_is_a_failure_not_a_skip` |
| F5 | **A panel with a hole was accepted silently.** A missing mid-session bar (halt or data gap) or a truncated session would shift the signal clock, the fill bar or the forced liquidation. `data.py` drops such sessions, but `run_backtest` accepted any `BarPanel`. | `backtest.py:169` | `probe-defects-unmodified.txt`: "DEFECT 1" | `validate_panel` requires each session to match the XNYS 5-minute grid exactly, with finite positive prices and non-negative volume | `test_noncontiguous_panel_is_refused` |
| F6 | **Default capital was $100,000.** Spec §4 says $25,000. | `backtest.py:27`, `cli.py:136` | "DEFECT 4" | Default `starting_capital=25_000`, whole shares (`--fractional-shares` to opt out) | `test_default_capital_is_spec_25k`, `test_whole_shares_by_default` |
| F7 | **`synthetic_panel` crashed above 6 symbols** (a 6-element beta vector), which blocks synthetic N>6 scaling instances. | `demo.py:26` | "DEFECT 3": broadcast error (6,) vs (8,) | Betas for any N. The first six are unchanged, so 6-symbol output is bit-identical. | `test_synthetic_panel_supports_more_than_six_symbols` |
| F8 | **The existing future-perturbation test could not see a look-ahead.** It scaled all later prices by 1.6, which leaves every later return unchanged except at one bar. | `tests/test_intraday.py:183-197` (removed) | sabotage S1: a forecast that peeks one bar ahead left it **green** (`sabotage-round-1.txt`) | Superseded by the owner-required test below and deleted | `test_future_price_perturbation_does_not_change_past` (red under S1) |

The owner's required test (spec §6, "deliberately modify future prices and verify past trading
decisions do not change") is `test_future_price_perturbation_does_not_change_past`, with three
cut points × all 9 classical methods. It compares decisions (target weights), forecasts, fills,
orders and equity before the cut, and it also asserts that the perturbation changed something
after the cut. Its companion, `test_fill_at_a_bar_open_uses_nothing_from_that_bar_but_its_open`,
covers what the strictly-before comparison cannot see: a fill at bar `t` that peeks at bar
`t`'s own close or volume.

**Honest note on "red before the fix".** On the unmodified tree the perturbation tests were red
only because `decisions` and `fills` did not exist yet. The causality property itself already
held (`probe-leak-unmodified.txt`). Their ability to fail is shown by sabotage (S1, S2, S11
below), not by a pre-existing leak.

### Sabotage round (disposable copy, one mutation at a time: `sabotage-round-2.txt`)

S1 forecast peeks one bar ahead → caught. S2 participation reads the fill bar's own volume →
caught by the bar-open test. S3 fill at the previous close instead of this open → caught.
S4 commission not debited → caught. S5 buys not capped by cash, with the engine's own guard
also removed → caught. S6 no end-of-day liquidation, with the engine's overnight assertion also
removed → caught. S7 contiguity guard removed → caught. S8 stress replaces slippage again →
caught. S9 conservative gate forced true → caught. S10 severe cheaper than conservative →
caught. S11 the test's own perturbation made the identity → caught. S12 fractional by default →
caught.

**NULL results:**
- S2 against the strictly-before perturbation test stays green. This is by construction, and is
  why the bar-open variant exists.
- Round 1, S3 (`sabotage-round-1.txt`) was green: the fill log hard-coded
  `reference_price = open`, and the synthetic generator opens every bar at the previous close.
  Fixed: the log now records the price actually used, the fixture has intra-session gaps, and
  the test recomputes every fill price from the market open and the cost model.

## Broken, and open: files owned by other agents (proposed fixes, not applied)

| # | file:line | defect | why it matters | proposed fix |
|---|---|---|---|---|
| O1 | `optimizer.py:198-202`, `:255-256`; benchmark shot count | **The benchmark's QAOA "zero gap" is guaranteed by sampling, not earned by the circuit.** Both QAOA functions return the best of `qaoa_shots` samples. At the benchmark sizes the feasible space is tiny next to the shot count (n=6, k=2: 15 states vs 256 shots). Measured (`measure_audit.txt`, 20 random QUBOs): optimum found by optimized XY-QAOA 20/20, by uniform random K-hot sampling with the same 256 shots 20/20. The chance that uniform sampling misses is 2.1e-8. | Any "QAOA matches exact" claim from `solver_benchmark_summary.csv` says nothing about the quantum algorithm. This is the central quantum-vs-classical question. | Report the probability mass on the optimum, the expected energy (approximation ratio) and time-to-target. Add a uniform-random-sampler baseline with the same shots. Keep shots ≪ C(n,k), or report solution quality as a function of shots. |
| O2 | `optimizer.py:167-173` | The X-mixer QAOA standardises energies over all 2^n states, including the penalty. The penalty dominates the variance, so feasible-state differences get a small phase. Measured mean feasible mass 0.545. | It handicaps X-mixer QAOA against XY, so the mixer comparison is not like-for-like. | Scale the penalty to the feasible-energy range (for example, max minus min feasible energy plus a margin), and document it |
| O3 | `benchmark.py:58` vs `optimizer.py:297` | The benchmark builds its `full_exact` reference with `max_cases=150`, but `choose('full_exact')` uses the default `100`. For C(n,k) in (100,150], e.g. n=10, k=3, the method errors and is recorded as infeasible (`benchmark-full-exact-cap.txt`). | A false infeasibility in the scaling study | Pass one cap through `OptConfig` |
| O4 | `optimizer.py:102` | `fit.mip_gap <= 1e-8` raises `TypeError` when HiGHS returns `mip_gap=None` (time limit with no bound) | A MILP time-out crashes the benchmark instead of being recorded | `fit.mip_gap is not None and …` |
| O5 | `data.py:44` | The timezone is inferred from the **first** row only. A file mixing naive and aware timestamps is mis-parsed. | Silent time shift | Parse all rows. Fail if some are tz-aware and some naive. |
| O6 | `data.py:260`, `:273` | One missing 5-minute bucket in **any** symbol drops the whole session for every symbol, up to 15% of sessions. Halt days and thin days are the volatile ones. | Sample-selection bias towards calm days. It is not reported in the metrics. | Report rejected sessions next to the results, and test whether the rejected days are more volatile (from daily data) |
| O7 | `data.py:31`, `:130` | `urllib3.Retry` on 429/5xx raises `RetryError` once exhausted, and that is reported as "Could not reach Alpaca … DNS/firewall" | A misleading diagnosis | Catch `RetryError` separately ("rate-limited / server error after N retries") |

## Needs improvement (not defects; recorded so nobody rediscovers them)

- **N1. Labels and embargo, when trained models land (spec §4).** A 30-minute target sampled
  every 5-minute bar gives labels that overlap by 5 of 6 bars. The training set for a decision
  at `t` must end at or before `t − horizon` (purge), with an embargo of at least one horizon
  after each validation fold. Normalisation statistics must be computed only on the training
  window.
- **N2. Partial fills.** A rebalance that breaches `max_participation` is rejected whole and the
  old portfolio is kept. That is conservative, but at $100k on the synthetic volume it silently
  removed 23 of 216 `topk` and 8 of 26 `spy` rebalances in the old demo, which is why the old
  and new demo `topk` returns differ (−2.11% vs −4.93%; the ledger itself agrees to 1e-5).
  Report the rejection count in the metrics, and consider clipping each leg to the cap.
- **N3. Fractional-mode micro-trades.** With `--fractional-shares`, cash residue makes
  sub-cent rebalances count as trades (SPY: 30 vs 20). Add a minimum trade notional.
- **N4. Metrics.**
  - `oos_annualized_return` (`backtest.py:233`) annualises 10 sessions (−31.9% in the old
    demo). Set it to NaN below about 60 sessions.
  - `oos_max_drawdown` uses daily closes only, so intraday troughs are invisible. Add a
    bar-level drawdown.
  - Sortino, Calmar, profit factor, exposure-adjusted return and monthly P&L (spec §8) are
    missing.
  - Forecast quality (realised versus predicted 30-minute return, IC) is not recorded
    separately from trading P&L (spec §4).
- **N5. Performance.** The engine runs at about 0.085 s per session with 8 methods and 6
  symbols (`measure_audit.txt`). A 2024 to 2026 run (about 700 sessions) takes about 60 s,
  and `--stress` reruns the full engine 8 more times (4 grid rows + 4 scenarios), about 9
  minutes. Forecasts (`mu`, `cov`) do not depend on costs and could be computed once.
  Decisions depend on holdings, so they cannot be cached across scenarios.
- **N6. The cost model is OHLCV-only.** Spread, slippage and impact are assumptions (labelled
  MODELED in every output), not measured from quotes. The scenario numbers are
  order-of-magnitude choices for liquid ETFs and need calibrating against NBBO before any claim.
  Alpaca charges no commission, so `commission_bps` stands in for regulatory sell-side fees
  (SEC Section 31, FINRA TAF). Check those rates at the time of use.
- **N7. README is stale on points this change touched** (not edited here; it is not in this
  agent's files): default capital $25k with whole shares; `--stress` now also writes
  `cost_scenarios.csv`; new outputs `fills.csv` and `decisions.csv`; README item 9 ("no partial
  fills") still holds; accounting is now a share/cash ledger.
- **N8. Multiple testing.** Nine methods are compared against SPY, and the audit gates one
  pre-chosen method (`milp_qubo`). Choosing the method after seeing the holdout invalidates it.
  The bootstrap p-value is unadjusted.
