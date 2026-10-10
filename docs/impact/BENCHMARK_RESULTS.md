# Track 1 — benchmark results (quantum vs classical, and trading vs baselines)

Every number below comes from a committed output file named in its row; nothing is estimated. QAOA everywhere is **ideal or shot-sampled simulation on a CPU** (Qiskit / qiskit-aer, or Qollab's built-in simulator) — not quantum hardware, not an IonQ run. Two questions are kept separate, as the owner's spec requires: (A) does QAOA solve the selection QUBO better or faster than classical solvers, and (B) does the QC-TRADE strategy make money out of sample after costs.

## A1. Solver scaling on synthetic instances (computational benchmark, not a trading result)

Source: `impact/outputs/scaling/summary.csv` (537 solves, 0 errors), `impact/outputs/scaling/not_run.csv`, plots `scaling_trading.png`, `scaling_hard.png`, `qaoa_amplification.png`; method and full tables in `vault/Reports/impact-research-solvers.md`. Recomputed from the committed trials on the final `main` (`evidence/integration/final-checks-67826d2.txt` §7). Median end-to-end seconds; in brackets, the share of runs whose decoded answer was the certified optimum. QAOA: p = 2 layers, COBYLA with 80 evaluations, 1,024 shots.

| regime | N | k | feasible portfolios | MILP (HiGHS) | greedy | annealing | random k-hot, 1,024 shots | QAOA-X | QAOA-XY | P(optimum) per shot vs random k-hot, X / XY |
|---|---|---|---|---|---|---|---|---|---|---|
| trading | 6 | 3 | 20 | 0.0087 | 0.0024 (100%) | 0.056 (100%) | 0.0024 (100%) | 0.47 (100%) | 0.73 (100%) | 1.35× / 4.84× |
| trading | 10 | 3 | 120 | 0.012 | 0.0037 (100%) | 0.094 (100%) | 0.0041 (100%) | 0.63 (100%) | 1.16 (100%) | 0.79× / 3.62× |
| trading | 15 | 3 | 455 | 0.016 | 0.0027 (100%) | 0.14 (100%) | 0.0029 (89%) | 1.71 (78%) | 3.79 (100%) | 0.63× / 3.82× |
| trading | 20 | 3 | 1,140 | 0.027 | 0.0049 (100%) | 0.18 (100%) | 0.0050 (56%) | 40.1 (33%) | 98.9 (89%) | 0.46× / 5.45× |
| trading | 30 / 50 / 100 | 3 | 4,060 / 19,600 / 161,700 | 0.054 / 0.14 / 0.54 | ≤ 0.0046 (100%) | ≤ 0.90 (100%) | 33% / 0% / 0% | not run | not run | — |
| hard | 20 | 4 | 4,845 | 0.036 | 0.014 (100%) | 0.19 (100%) | 0.017 (22%) | 39.2 (11%) | 105 (44%) | 0.42× / 4.18× |
| hard | 50 / 100 | 10 / 20 | 1.0e10 / 5.4e20 | 0.18 / 0.84 (certified) | 0.040 / 0.033 (100%) | 0.48 / 0.92 (100%) | 0% | not run | not run | — |

**Not run, and why** (`not_run.csv`): QAOA at N ≥ 30 needs a 2^N × 16-byte statevector = 17.2 GB at N = 30 against a 4 GB budget on a shared laptop; N = 21–27 would fit but take about 6 to 60+ minutes per run. Exact enumeration is capped at 1e6 supports; above it the reference is the certified MILP optimum.

**Control that the benchmark is not trivially easy:** on random Gaussian QUBOs the same MILP times out at 60 s at N = 100 (gap 3.0–3.7); on the portfolio "hard" instances it certifies N = 100 at the root node in about 0.4 s. The easiness belongs to the portfolio instances.

**Verdict A1:** classical solvers win on every instance measured. Greedy found the certified optimum in 100% of runs up to N = 100 in at most 0.04 s; MILP certified every instance. The cardinality-preserving XY mixer concentrates probability on the optimum 3–7× better than uniform random k-hot guessing per shot; the X mixer with a penalty does worse than random from N = 10. Reaching the optimum with 99% confidence at N = 20 took QAOA 207–819 s of simulation against about 0.005–0.014 s for greedy. In all 144 QAOA runs the angle optimiser used its full 80-evaluation budget without converging. No quantum advantage was observed.

## A2. Same-instance benchmark on real-data snapshots

Source: `impact/outputs/real_bench_noDIA/solver_benchmark_summary.csv` and `solver_benchmark_trials.csv` (QUBOs built from real Alpaca SIP data, universe SPY QQQ IWM TLT GLD, sub-universe n = 4, 36 trials per method). Every method, including both QAOA variants and the uniform random k-hot control, reached the exact optimum (median QUBO gap 0, refined gap 0). Median seconds: exact 0.0002, greedy 0.0002, random k-hot 0.0003, MILP 0.0042, annealing 0.0088, QAOA-X 0.082, QAOA-XY 0.109. At this size every method is exact, and QAOA is 20–500× slower.

## A3. The Qollab submission instance (n = 6, k = 2, synthetic)

Source: `evidence/impact-qollab/run-local.txt`, `evidence/impact-qollab/seed-sweep.txt`, re-run in `evidence/integration/final-checks-67826d2.txt` §4. All six solvers select the exact optimum (IWM+TLT). Share of shots on the optimum over seeds 1–10:

| n, k | QAOA-XY | QAOA-X | uniform random k-subset |
|---|---|---|---|
| 6, 2 | 0.221 | 0.044 | 0.067 |
| 6, 3 | 0.143 | 0.047 | 0.050 |
| 8, 4 | 0.116 | 0.011 | 0.014 |

## B. Trading: QC-TRADE vs classical baselines, real data, 2026 out of sample

Pre-registered in `impact/PREREGISTRATION_2026-10-10.md` (commit `249aa15`) before any real-data return was seen. Data: Alpaca SIP 1-minute bars, 2024-01-01..2026-10-09, manifest SHA-256 `c579b58d…f892`. Out of sample: 2026-01-02..2026-10-09. Capital $25,000, whole shares, next-bar execution, no overnight positions. All costs are MODELED from OHLCV, not observed quotes.

**Primary analysis (6 ETFs incl. DIA): refused.** The data-quality gate rejected 280 of 696 sessions (40.2%) against 15% allowed (`impact/outputs/real_full_primary/REFUSED.txt`). The threshold was not loosened.

**Sensitivity analysis (5 ETFs, DIA removed for data quality, pre-registered):** 189 OOS sessions. Source `impact/outputs/real_full_noDIA/` (`metrics_oos.csv`, `paired_bootstrap_vs_spy.csv`, `cost_stress_grid.csv`, `cost_scenarios.csv`).

| method | net return, base costs | Sharpe | max drawdown | trades | fees + costs | mean daily excess vs session-flat SPY, bps [95% block-bootstrap CI] |
|---|---|---|---|---|---|---|
| QC-TRADE, MILP selection | −16.9% | −2.44 | −18.4% | 1,837 | $2,946 | −6.7 [−13.0, −0.5], p = 0.03 |
| QC-TRADE, exact / greedy / annealing | −16.9% | −2.44 | −18.4% | 1,835 | $2,950 | −6.7 [−12.8 to −13.3, −0.1 to −0.7], p = 0.03–0.05 |
| top-K momentum | −42.3% | −6.99 | −42.3% | 2,231 | $2,867 | −26.0 [−32.0, −19.5] |
| minimum variance | −8.5% | −2.27 | −12.1% | 840 | $1,880 | −1.8 [−7.7, +4.1] |
| equal weight | −8.9% | −1.51 | −12.0% | 529 | $1,777 | −1.9 [−5.5, +1.7] |
| session-flat SPY | −5.5% | −0.87 | −8.6% | 378 | $1,805 | 0 (baseline) |
| cash | 0.0% | — | 0.0% | 0 | $0 | +2.9 [−4.9, +9.8] |

**Cost scenarios, QC-TRADE (MILP) vs session-flat SPY** (`cost_scenarios.csv`): optimistic −6.9% vs −0.2%; base −16.9% vs −5.5%; conservative −31.3% vs −13.3%; severe stress −66.3% vs −36.8%. **Extra slippage per side** 0 / 1.5 / 5 / 10 bps (`cost_stress_grid.csv`): −16.9% / −26.1% / −45.2% / −63.4%.

**Quantum-vs-classical trading ablation:** the four classical selection solvers produce near-identical portfolios and returns (they find the same optimum), so the choice of discrete optimiser does not change the trading outcome at this size. QAOA was not run inside the backtest: with every exact method already at the optimum, QAOA could at best reproduce the same portfolios at higher cost.

**Verdict B:** not validated under the pre-registered rule. QC-TRADE lost money in 2026 under every cost scenario, and it is statistically significantly worse than holding SPY during the same sessions. The losses come mostly from trading costs on ~1,800 trades (fees and modelled costs ≈ 12% of capital), on a signal that did not cover them.

## Caveats that apply to every number
- One out-of-sample period (2026, 189 sessions), one universe, one parameter set; no regime breakdown was run.
- Costs are modelled, not taken from quotes; fills are bar-open approximations.
- The no-DIA universe was chosen after seeing data quality (not returns); the rejected TLT sessions are more volatile than kept ones, so the kept sample is biased toward calmer TLT days.
- The pre-registered run used the code before the solver merge; the benchmark run used the merged code. Their MILP rows differ slightly (−16.90% vs −16.81%, one trade), consistent with the new MILP formulation; every other row is identical.
