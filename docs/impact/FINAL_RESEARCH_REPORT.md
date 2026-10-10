# QC-TRADE / Track 1 (Quantum Impact) — final research report

2026-10-10. Answers the owner's seven questions from committed outputs only. Detailed numbers: `docs/impact/BENCHMARK_RESULTS.md`. How each piece was checked and merged: `docs/impact/INTEGRATION_AUDIT.md`. What is left to do: `docs/impact/SUBMISSION_CHECKLIST.md`. No orders of any kind were placed, no IonQ or other paid job was sent, and nothing was pushed.

## 1. Does the code actually work?

Yes, for everything that could be run here. On the final `main` (`evidence/integration/final-checks-67826d2.txt`, Python 3.13, qiskit 2.5.2):

| check | result |
|---|---|
| QC-TRADE test suite (`impact/`) | 136 passed (28 at import; +15 backtest integrity, +54 solvers, +39 data pipeline, net of replaced tests) |
| byte-compile and import of every module | OK |
| exact enumeration = MILP energy, greedy never below exact, 20 seeded instances | 20 / 20 |
| Qollab project end-to-end (`impact-qollab/`) | exit 0, 1.1 s, exactly 1 backend job |
| independent QAOA circuit checks (Dicke state, cost layer, XY cardinality, a control that must fail) | pass |
| backtest leakage and accounting tests | 16 passed |
| synthetic end-to-end demo | runs (labelled non-evidence) |
| scaling summary recomputed from committed trials | identical |
| real read-only Alpaca pipeline (smoke and full) | `SUMMARY: OK … orders=0` |

The tests are not vacuous: each agent broke its own code deliberately and the tests caught it (backtest 12/12, solvers 18/18, data 25/25, Qollab gate 7/7).

## 2. Which experiments ran on real market data?

- The read-only Alpaca paper checks (account, clock, SIP and IEX entitlement): both feeds allowed (`evidence/integration/alpaca-check-2026-10-10.txt`).
- The full download: Alpaca SIP 1-minute bars, raw, SPY QQQ IWM DIA TLT GLD, 2024-01-01..2026-10-09: 3,010,839 minute rows, 696 sessions, 280 rejected by the completeness checks (DIA 262, GLD 32, TLT 5), manifest SHA-256 `c579b58d70a646aed7abdf37e4615b4772483e36c6e63b427dab04d3e856f892` (`evidence/integration/alpaca-fetch-full-2026-10-10.txt`).
- The pre-registered 2026 out-of-sample backtest (`impact/PREREGISTRATION_2026-10-10.md`, committed before any real-data return was seen): primary 6-ETF analysis refused by the data-quality gate (40.2% of sessions rejected > 15% allowed); sensitivity 5-ETF analysis (DIA removed for data quality) ran with the full cost-stress grid and the four cost scenarios (`impact/outputs/real_full_noDIA/`).
- The same-instance solver benchmark on QUBOs built from the real data (`impact/outputs/real_bench_noDIA/`).

Everything else — the solver scaling study, the Qollab project's instance, the demo — is synthetic and labelled so.

## 3. Did QC-TRADE make money out of sample after costs?

**No.** Over 189 out-of-sample sessions in 2026 (5 ETFs, $25,000, next-bar execution, no overnight positions, modelled costs):

- QC-TRADE (MILP selection): **−16.9% net**, Sharpe −2.44, max drawdown −18.4%, 1,837 trades, about $2,950 in fees and modelled costs.
- Against session-flat SPY (−5.5%): mean daily excess **−6.7 bps, 95% block-bootstrap CI [−13.0, −0.5], p = 0.03**, i.e. significantly worse.
- It loses under every cost scenario: optimistic −6.9%, base −16.9%, conservative −31.3%, severe −66.3%.
- Under the pre-registered decision rule (positive under conservative costs, beats the baseline, bootstrap lower bound above zero) it fails all three conditions. **Not validated.**

## 4. Did quantum / QAOA beat the best classical baseline?

**No, on every instance measured.**

- Synthetic scaling, N = 6..100: greedy found the certified optimum in 100% of runs in ≤ 0.04 s; HiGHS MILP certified every instance (N = 100 in < 1 s). QAOA (Qiskit, simulated) needed 0.5 s at N = 6 and about 40–105 s at N = 20, and did not always return the optimum (X mixer 33%, XY mixer 89% at N = 20, trading regime).
- Per shot, the XY mixer puts 3–7× more probability on the optimum than uniform random k-hot guessing; the X mixer is worse than random from N = 10. Time to the optimum with 99% confidence at N = 20: 207–819 s for QAOA vs about 0.01 s for greedy.
- Real-data instances (n = 4): every method is exact; QAOA is 20–500× slower.
- Trading ablation: all classical selection solvers produce the same portfolios, so the discrete optimiser does not change the trading result at this size.
- QAOA at N ≥ 30 was not run (17.2 GB statevector against a 4 GB budget). This is simulation on a CPU throughout: it says nothing about quantum hardware, for or against.

## 5. What evidence supports those conclusions?

- Committed outputs: `impact/outputs/real_full_noDIA/` (metrics, daily returns, bootstrap, stress grid, cost scenarios, weights, forecasts, order costs, equity curves), `impact/outputs/real_bench_noDIA/`, `impact/outputs/real_full_primary/REFUSED.txt`, `impact/outputs/scaling/` (537 solves, plots), `evidence/impact-qollab/`.
- The pre-registration commit `249aa15` precedes every real-data result.
- Agent reports: `vault/Reports/impact-qollab-qaoa.md`, `impact-research-audit.md`, `impact-research-solvers.md`, `impact-research-data.md`; the audit `impact/AUDIT.md`.
- Raw prices are not committed (licensed): `fills.csv` and the data cache stay local and are regenerated from the manifest hash and the pre-registered commands.

## 6. What remains untested?

- The Qollab project on Qollab itself: the Qiskit half has never run in Pyodide (stock Pyodide cannot install Qiskit 2.x; Qollab ships its own build). Owner action.
- Any IonQ run (simulator or hardware), and whether `qiskit-ionq` accepts two circuits in one job; whether IonQ simulators are free for a signed-in account.
- Quote-based spreads and fills (only OHLCV was used; every cost is modelled); IEX vs SIP discrepancies.
- Regime breakdown, parameter sensitivity, multiple-testing correction across variants, other periods or universes, adjusted-price variants. The spec asks for these; they were not run.
- Other predictive models from the spec (volatility-adjusted momentum, ridge/elastic-net, gradient-boosted trees): not implemented; the strategy uses the original shrunk-momentum forecast.
- QAOA beyond N = 20; noisy simulation of the backtest's QAOA.
- Paper trading: deliberately not built (spec §11). **The system is not ready for paper trading**: the strategy has no edge to test forward.

## 7. Is the Qollab Track 1 submission ready?

**Code: yes. Submission: not yet.**

- `impact-qollab/` runs locally end to end, passes its own gates and the independent circuit checks, and passes every rule of `scripts/gates/qollab-submission.mjs` except the YouTube demo link, which cannot exist until the video is recorded.
- The project page is complete and honest: run steps, the benchmark table, the verdict, limitations, prior work (QC-TRADE developed with AI assistance on 2026-10-10; arXiv:2504.07844 credited only for the two-stage structure — it is about proton-therapy beam angles), the real-data finding, and the verbatim attribution.
- Remaining, all owner actions (`docs/impact/SUBMISSION_CHECKLIST.md`): push to GitHub, create and run the project on Qollab, decide on IonQ (free or not), record and link the video, publish, submit before 2026-10-11 19:00 ET.

## Implemented, tested, demonstrated, proposed

| item | implemented | tested | demonstrated on real data | proposed only |
|---|---|---|---|---|
| Qiskit QAOA (X, XY) + classical solvers, Qollab project | yes | yes | n/a (synthetic by design) | |
| Backtest ledger, next-bar fills, cost scenarios, leakage tests | yes | yes | yes (2026 OOS) | |
| HiGHS MILP + RLT, greedy, annealing, random control, scaling to N = 100 | yes | yes | n = 4 real snapshots | |
| Read-only Alpaca pipeline, Parquet cache, manifest, calendar, completeness | yes | yes | yes (smoke + full) | |
| Regime breakdown, sensitivity analysis, multiple-testing control | | | | yes |
| Ridge / elastic-net / gradient-boosted forecasts | | | | yes |
| Quote/NBBO execution simulation | | | | yes |
| Paper-order routing | | | | not authorised |
