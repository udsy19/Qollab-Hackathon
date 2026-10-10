---
type: report
status: current
date: 2026-10-10
updated: 2026-10-10
owner: research-solvers
tags:
  - impact
  - qc-trade
  - qaoa
  - benchmark
---

# Impact: quantum vs classical solvers for QC-TRADE's Stage A, and how they scale (plan row 5)

Spec sections 5 and 9 ([[Design/impact-qc-trade-spec]]) on branch `worktree-agent-af390822910e72793`. The instances are **synthetic** (seeded factor model), so this is a computational benchmark, not a trading result. **All QAOA numbers come from an ideal statevector simulated on a laptop CPU** (Qiskit circuits, qiskit-aer, 1 thread). Nothing ran on quantum hardware, and no QAOA runtime here is a quantum runtime.

## Vault check

- **Read:** `vault/AGENTS.md`, [[Design/impact-qc-trade-spec]] (in full; sections 5 and 9 govern this row), [[Research/impact-qc-trade-fit]] (gap G1: no Qiskit), [[Plan]] row 5, [[Index]], and `vault/Decisions/` (only 0001; nothing governs solvers).
- **Already known:** the imported code warned that 2–9 assets "cannot demonstrate an asymptotic quantum advantage" (`impact/EXAMPLE_EXPERIMENT_PLAN.md`). The research-audit agent's findings O1–O4 (`impact/AUDIT.md` on `worktree-agent-a555f850f32975121`) are all addressed below.
- **Reused:** `qubo_matrix`, `refine`, `portfolio_objective`, `full_exact`, `choose`, `OptConfig`, `benchmark_solvers`, and the McCormick MILP (extended, not forked).
- **Stale:** `impact/README.md` line 208 still describes the NumPy X-mixer QAOA. README is not in this agent's files (see Open questions).

## TL;DR: the verdict

**Classical optimisation wins on every instance we could measure, and by four to five orders of magnitude in time-to-target.** For this financial QUBO:

1. **The problem is classically easy.** On the 537 synthetic solves, greedy swap search found the certified optimum in **100%** of runs at every size up to N = 100, k = 20, in at most 0.04 s. HiGHS MILP with RLT cuts **certified** every instance (66/66), at N = 100 in 0.38–0.93 s at the root node. A non-financial control (random Gaussian QUBO) does defeat the same MILP at N = 100 (60 s time-out, gap 3.0–3.7), so the easiness belongs to the portfolio instances, not to a weak test.
2. **XY-mixer QAOA does something real per shot, but it does not pay.** Its probability of the optimal portfolio is **3–7x** that of a uniform random k-hot guess (median of 9 runs, N = 6–20). But producing that distribution took 80 full statevector simulations: **99–105 s at N = 20**, against 0.005–0.014 s for greedy. The time to reach the optimum with 99% confidence at N = 20 was 207 s (trading) and 819 s (hard), against 0.005 s and 0.014 s for greedy.
3. **X-mixer (penalty) QAOA is worse than random guessing.** Per shot, it is 0.42–0.79x the uniform k-hot sampler at every N ≥ 10. The provably safe cardinality penalty dominates the cost Hamiltonian, so 39–65% of the probability mass stays on infeasible strings.
4. **Nothing beyond N = 20 is simulable here.** At N = 30 a statevector needs 17.2 GB, over the 4 GB budget. For N = 21–27 it fits in memory, but the extrapolated time is 6–60+ min per run. The classical solvers ran up to N = 100.

No quantum advantage, in solution quality or in time, was observed. The comparison gave QAOA its standard form and audited controls; see Limitations for what would give it more.

## What was built

| file | change |
|---|---|
| `impact/qc_trade/qaoa.py` (new) | Qiskit QAOA. The QUBO is mapped to an exact Ising cost layer (RZ + RZZ), normalised by its uniform-superposition standard deviation. **X mixer:** \|+>ⁿ start, RX mixer, and a provable cardinality penalty `P = max_i(\|Q_ii\| + 2Σ_j\|Q_ij\|)`, which keeps the penalised ground state k-hot and equal to the constrained optimum (proof in the docstring; tested by brute force). **XY mixer:** a Dicke state \|D(n,k)> prepared by the Bärtschi–Eidenbenz O(nk) circuit, with a ring of `XXPlusYYGate` mixers. COBYLA (maxiter 80, p = 2) minimises the exact expectation. Decoding draws 1024 seeded shots and keeps the feasible one with the lowest **true** x'Qx. Each run reports P(optimum), the approximation ratio, the same-shot uniform baselines (audit O1), the fitted angles, depth, the multi-qubit gate count, and init/optimise/decode times. |
| `impact/qc_trade/optimizer.py` | The NumPy statevector QAOAs are **deleted**: the Qiskit path replaces them, and a NumPy statevector survives only as the independent test oracle in `tests/test_solvers.py`. Exact enumeration is vectorised (cap 1e6 supports). The MILP gains **RLT cuts** Σ_{j≠i} z_ij = (k−1)y_i and records a time-out with no gap as uncertified (O4). Greedy and annealing move in O(n) per step through incremental Qx. New **`random_khot`** control. `choose()` reports construct / solve / refine / total seconds. One `full_exact_max_cases` (2000) serves both the solver and the benchmark reference (O3). |
| `impact/qc_trade/scaling.py` (new) | Seeded instance generator. A run plan that **records each refusal with its reason**. Every solve runs in a fresh process (so peak RSS is attributable), with tracemalloc, a JSONL checkpoint and resume. Also the summary (references, gaps, TTT99, seed spread), the plots, and the MILP hardness probe. |
| `impact/qc_trade/benchmark.py` | The real-snapshot benchmark gains `random_khot`, the phase timings and the O1 columns. The QAOA size cap is now a parameter (`qaoa_max_n=12`). |
| `impact/tests/test_solvers.py` (new) | 54 tests: Ising mapping exact on every bitstring; penalty ground state k-hot and optimal (12 instances); Dicke circuit uniform over k-hot (5 sizes); **Qiskit circuit equals the NumPy oracle amplitude for amplitude** (both mixers); exact = both MILP formulations = brute force; MILP certifies at N = 30; every solver feasible and never below exact; QAOA decodes the lowest true energy; seed determinism; refusal reasons; O1, O3 and O4. |
| `impact/requirements.txt`, `pyproject.toml` | `qiskit==2.5.2`, `qiskit-aer==0.17.2`. Aer earns its place: it is **18x** faster than `qiskit.quantum_info.Statevector` at N = 20 (0.43 s vs 7.98 s per evaluation, same probabilities to 1e-17). |

### Same objective, same constraints (spec section 5)

Every Stage-A solver minimises the **same** x'Qx (`qubo_matrix`: the equal-weight return, covariance and turnover proxy) over the **same** set {x ∈ {0,1}ⁿ, Σx = k}:

- **Exact, MILP, greedy, annealing, random k-hot and XY-QAOA** stay inside the k-hot set by construction.
- **X-QAOA is the one formulation difference.** It minimises x'Qx + P(Σx−k)², which equals x'Qx plus a constant on the feasible set. P is the smallest value for which the penalised optimum is provably the constrained optimum, and infeasible samples are discarded at decoding.
- **Stage B** (`refine`, SLSQP with true L1 turnover) is applied identically to every Stage-A answer.
- **The proxy is not the full objective.** Stage A optimises an equal-weight proxy, not the refined portfolio objective. Against full enumeration of every support plus refinement, the QUBO optimum gave the best refined portfolio in **20 of 21** instances where enumeration was possible. In the one miss (hard, N = 15), the loss was **0.017 bp** of objective.

## The scaling table

Median end-to-end seconds (construction, initialisation, optimisation, decoding and continuous refinement); in brackets, the share of runs that hit the certified optimum. Each row is 3 instances; stochastic methods get 3 seeds each (9 runs). The "P(opt) vs k-hot" column is the per-shot probability of the optimal portfolio divided by that of a uniform random k-hot sample: above 1 beats random guessing. "Approx ratio" is (E_worst − ⟨E⟩)/(E_worst − E*) of the feasible-conditioned QAOA output; uniform sampling gives the value after "vs".

| regime | N | k | C(N,k) | exact | MILP | greedy | anneal | random k-hot (1024) | QAOA-X | QAOA-XY | P(opt) vs k-hot, X / XY | approx ratio X / XY vs uniform |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| trading | 6 | 3 | 20 | 0.0023 | 0.0087 | 0.0024 (100%) | 0.056 (100%) | 0.0024 (100%) | 0.47 (100%) | 0.73 (100%) | 1.35 / 4.84 | 0.56 / 0.75 vs 0.50 |
| trading | 10 | 3 | 120 | 0.0043 | 0.012 | 0.0037 (100%) | 0.094 (100%) | 0.0041 (100%) | 0.63 (100%) | 1.16 (100%) | 0.79 / 3.62 | 0.53 / 0.64 vs 0.49 |
| trading | 15 | 3 | 455 | 0.0031 | 0.016 | 0.0027 (100%) | 0.14 (100%) | 0.0029 (89%) | 1.71 (78%) | 3.79 (100%) | 0.63 / 3.82 | 0.49 / 0.58 vs 0.46 |
| trading | 20 | 3 | 1,140 | 0.0058 | 0.027 | 0.0049 (100%) | 0.18 (100%) | 0.0050 (56%) | 40.1 (33%) | 98.9 (89%) | 0.46 / 5.45 | 0.51 / 0.59 vs 0.50 |
| trading | 30 | 3 | 4,060 | 0.0067 | 0.054 | 0.0025 (100%) | 0.28 (100%) | 0.0053 (33%) | not run | not run | | |
| trading | 50 | 3 | 19,600 | 0.022 | 0.14 | 0.0024 (100%) | 0.45 (100%) | 0.0089 (0%) | not run | not run | | |
| trading | 100 | 3 | 161,700 | 0.16 | 0.54 | 0.0046 (100%) | 0.90 (100%) | 0.0069 (0%) | not run | not run | | |
| hard | 6 | 2 | 15 | 0.0019 | 0.0087 | 0.0022 (100%) | 0.056 (100%) | 0.0021 (100%) | 0.46 (100%) | 0.64 (89%) | 0.85 / 2.97 | 0.54 / 0.76 vs 0.52 |
| hard | 10 | 2 | 45 | 0.0028 | 0.012 | 0.0029 (100%) | 0.092 (100%) | 0.0031 (100%) | 0.64 (100%) | 0.99 (100%) | 0.56 / 4.46 | 0.41 / 0.63 vs 0.40 |
| hard | 15 | 3 | 455 | 0.0050 | 0.017 | 0.0047 (100%) | 0.14 (100%) | 0.0048 (89%) | 1.68 (67%) | 3.79 (100%) | 0.48 / 7.48 | 0.46 / 0.60 vs 0.45 |
| hard | 20 | 4 | 4,845 | 0.019 | 0.036 | 0.014 (100%) | 0.19 (100%) | 0.017 (22%) | 39.2 (11%) | 105 (44%) | 0.42 / 4.18 | 0.45 / 0.57 vs 0.45 |
| hard | 30 | 6 | 593,775 | 0.67 | 0.080 | 0.030 (100%) | 0.30 (100%) | 0.023 (0%) | not run | not run | | |
| hard | 50 | 10 | 1.0e10 | not run | 0.18 | 0.040 (100%) | 0.48 (100%) | 0.033 (0%) | not run | not run | | |
| hard | 100 | 20 | 5.4e20 | not run | 0.84 | 0.033 (100%) | 0.92 (100%) | 0.057 (0%) | not run | not run | | |

**Peak memory.** Peak process RSS, including the ~115 MB Python + Qiskit import baseline, was 115–116 MB for greedy and annealing at every N. MILP reached 191 MB at N = 100, and QAOA reached 197–203 MB at N = 20. The share attributable to QAOA at N = 20 is 82–87 MB.

**Stability.** Seed-to-seed spread of the relative QUBO gap is 0 for greedy, MILP, exact and annealing. For QAOA at hard N = 20 it is 0.43 (X) and 0.84 (XY); at small N, XY missed the optimum on 1 of 9 runs (hard N = 6). COBYLA reached its 80-iteration budget without converging in every QAOA run (`qaoa_success` = 0 in all 144). The diagnosis at hard N = 6 shows the angles lowered the expectation (−0.66 → −1.13 in normalised units) but piled mass onto near-optimal strings. **Minimising ⟨H⟩ is not maximising P(optimum).**

**Where QAOA's time goes (N = 20, median).**

| mixer | init (circuit + transpile) | optimise (80 Aer evaluations) | decode | refine | depth | multi-qubit gates |
|---|---|---|---|---|---|---|
| X | 0.25 s | 38–39 s | 0.5 s | 0.02 s | 62 | 380 |
| XY | 0.26–0.27 s | 97–103 s | 1.2–1.3 s | 0.02 s | 391–455 | 582–630 |

Plots: `impact/outputs/scaling/scaling_trading.png`, `scaling_hard.png` (runtime, TTT99, peak RSS and QUBO gap against N), and `qaoa_amplification.png` (P(opt) against the k-hot control).

### Where the strong classical baseline does get hard (`milp_probe.csv`)

| instances | N = 50, k = 10 | N = 100, k = 20 |
|---|---|---|
| financial "hard", MILP + RLT | 0.035–0.037 s, root node | 0.38–0.41 s, root node |
| financial "hard", McCormick only | 0.49–1.12 s | 4.2–25.6 s, 5–103 nodes |
| random Gaussian QUBO, MILP + RLT | 9.9–35.7 s, 87–1564 nodes | **time-out 60 s**, gap 3.0–3.7 |
| random Gaussian QUBO, McCormick only | **time-out 60 s**, gap 0.66–1.40 | **time-out 60 s**, gap 6.5–23 |

The covariance-plus-return structure (a PSD factor model with a dominant linear term) makes the portfolio QUBO near-separable: its LP relaxation is integral at the root. That, not a weak MILP, is why classical wins so easily. A credible quantum-advantage study would need a financial problem whose instances look like the bottom rows. We did not find one in this formulation.

## What did not run, and why (`not_run.csv`)

| configuration | reason |
|---|---|
| QAOA X and XY, N = 30, 50, 100 (both regimes) | The statevector needs 2^N × 16 B = 17.2 GB at N = 30 (1.8e7 GB at 50, 2e22 GB at 100), against the 4 GB budget for this shared laptop. |
| QAOA, 21 ≤ N ≤ 27 | Not in the planned sizes. It would fit in memory (≤ 2.1 GB), but the extrapolation from the measured 0.43 s per evaluation at N = 20 gives about 6 min per run at N = 22 and over an hour at N = 26. |
| exact enumeration, hard N = 50 and 100 | C(50,10) = 1.0e10 and C(100,20) = 5.4e20 supports exceed the 1e6 cap. The reference there is the **certified** MILP optimum. |
| `full_exact` (full-objective reference), C(N,k) > 2000 | Each support needs one SLSQP solve. The portfolio-gap reference there is the best known among solvers (labelled `best_known` in `trials.csv`). |
| quantum hardware, noise models, IonQ | Out of scope for this row. That is plan row 3 (`impact-qollab/`, agent qollab-qaoa). |

All 537 planned runs completed: 0 errors and 0 infeasible answers (`trials.csv`).

## Limitations (what a sceptic should push on)

- **Synthetic instances.** The factor-model scales were chosen as plausible 30-minute numbers, not fitted to Alpaca data. The real-snapshot path, `benchmark_solvers` on a `BarPanel`, is wired and tested but was not run on real bars here (data is row 6).
- **QAOA was run in its standard form:** p = 2, COBYLA with 80 evaluations, one random start, expectation loss. Larger p, warm starts, parameter transfer, CVaR loss or more evaluations could raise P(optimum). Each also costs more simulated evaluations, and the classical solvers are already at the certified optimum in milliseconds, so none of these can change the verdict on these instances.
- **Runtime of a simulation is not a quantum runtime.** The only hardware-relevant numbers are circuit depth, multi-qubit gate count and P(optimum) per shot. At N = 20, XY-QAOA needs a depth of 391–455 with 582–630 multi-qubit gates (Dicke preparation included), before any transpilation to native gates.
- **TTT99 for QAOA** assumes the 80-evaluation optimisation is repeated per attempt. Amortising the angles across instances, as parameter transfer would, would cut that cost. It would not close a 10^4–10^5x gap.
- **Spec section 9 also asks which financial problem is more promising.** This was reasoned, not measured: optimal execution scheduling is a continuous, convex problem in its standard (Almgren–Chriss) form and offers even less room. Problems with hard combinatorial structure, such as lot-size or round-lot integer constraints, many-asset cardinality with sector caps, or index tracking with integer holdings, are more plausible places to look. Any of them would first have to pass the MILP-hardness probe above.

## Evidence

- `cd impact && python -m pytest -q` → exit 0 → `82 passed` (`evidence/impact-research-solvers/pytest.log`)
- `python evidence/impact-research-solvers/sabotage.py impact <scratch>` → exit 0 → `SABOTAGE 18/18 RED` (`evidence/impact-research-solvers/sabotage.log`)
- `cd impact && python -m qc_trade.scaling --out outputs/scaling --workers 3` → exit 0 → 537 rows, 0 errors (`impact/outputs/scaling/{trials.jsonl,trials.csv,summary.csv,not_run.csv,manifest.json,*.png}`)
- `python -m qc_trade.scaling --out outputs/scaling --workers 2 --milp-probe` → exit 0 → `impact/outputs/scaling/milp_probe.csv`
- Baseline before any change: `python -m pytest -q` → `28 passed`.

## Related

- [[Design/impact-qc-trade-spec]] · [[Research/impact-qc-trade-fit]] · [[Plan]] row 5 · `impact/AUDIT.md` (research-audit, findings O1–O4)
