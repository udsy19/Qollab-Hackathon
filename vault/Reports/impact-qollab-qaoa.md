---
type: report
status: current
date: 2026-10-10
updated: 2026-10-10
owner: qollab-qaoa
tags:
  - impact
  - qc-trade
  - qollab
  - qaoa
---

# Impact track: the Qollab project `impact-qollab/` (QAOA in Qiskit vs classical solvers)

## Vault check

- **Read:** [[AGENTS]], [[Research/impact-qc-trade-fit]], [[Research/qollab-platform-and-submission]] (§1, §2, §6 B–D), [[Design/impact-qc-trade-spec]] (§5, §9), `.claude/rules/hackathon-eligibility.md`, `templates/qollab-project/`, `scripts/gates/qollab-submission.mjs`, the coordinator's page draft `docs/impact/page-and-video.md` (main checkout).
- **Already known:** the fit note's gaps G1 (no Qiskit), G4 (one job per run), G5 (Pyodide deps, MILP unknown), G6 (no `main.py`), G7 (novelty category). This work closes G1, G4, G6 and G7 and answers the MILP half of G5.
- **Reused:** the QUBO, exact, MILP, greedy, annealing and SLSQP sizing from `impact/qc_trade/optimizer.py` (commit 89006f4), vendored into `impact-qollab/qctrade/solvers.py` with the maths unchanged (a justified fork: Qollab needs a self-contained folder). The page wording, novelty category and credits paragraph come from `docs/impact/page-and-video.md`. `where.mjs qaoa --branches` found no Qiskit QAOA anywhere (only the NumPy one in `impact/`).
- **Stale:** none found. One addition to the platform note: Qollab's runtime doc (read 2026-10-10 with defuddle, https://qollab.xyz/learn/docs/runtime-environment § Importing your own files) says the project root is the working directory and first on `sys.path`, so `main.py` can import packages in subfolders. The fit note listed this as "to be checked" (G6).

## TL;DR

`impact-qollab/` is a Qollab Python project that builds a k-of-n portfolio-selection QUBO on six SYNTHETIC ETFs, tunes two Qiskit QAOA circuits locally with `Statevector` (X mixer + cardinality penalty; XY ring mixer from a Dicke state), sends both in ONE `backend.run`, and prints a table against exact enumeration, MILP (HiGHS), greedy and simulated annealing: objective, feasibility, gap, runtime, plus stage-B sizing. It runs locally in 1.1 s (`evidence/impact-qollab/run-local.txt`). Over 10 seeds the XY mixer puts 0.221 / 0.143 / 0.116 of its shots on the optimum at (n,k) = (6,2) / (6,3) / (8,4), against 0.067 / 0.050 / 0.014 for a random k-subset; the penalised X mixer does no better than random (0.044 / 0.047 / 0.011). Every classical solver hits the optimum on every seed in milliseconds. No advantage is claimed. Not yet run on Qollab itself, and not on IonQ.

## What was built

- `impact-qollab/main.py`: one-line typed `def main(n_assets: int = 6, k: int = 2, reps: int = 2, shots: int = 1024, seed: int = 7, risk_aversion: float = 6.0)`; uses the pre-created `backend` (BasicSimulator only inside `except NameError`); one `backend.run` call site; seeds the built-in simulator's sampling (`seed_simulator`, only when the backend is `basic_simulator`); offers a JSON copy via `js.sendFile` on Qollab.
- `impact-qollab/qctrade/qaoa.py`: QUBO to Ising, cost layer (`RZ`, `RZZ`), X mixer (`RX`), XY ring mixer (`XXPlusYYGate`), deterministic Dicke-state preparation (Bärtschi and Eidenbenz; the doubly controlled RY written as two Toffolis), COBYLA angle tuning on `Statevector` with 3 seeded starts, counts decoding that accepts binary or hex keys.
- `impact-qollab/qctrade/instance.py` and `data/etf_stats_synthetic.json`: SYNTHETIC stats for 8 tickers (SPY QQQ IWM DIA TLT GLD EFA HYG), from a seeded simulation of 756 days with hand-chosen vols and correlations, mu shrunk halfway to the hand-chosen drift. The loader validates shape, symmetry and PSD, and is replaceable by a derived-statistics JSON by changing one string literal; if the file cannot be read it regenerates the same data in code.
- `impact-qollab/README.md`: the project page, every template section filled; the demo-video line says the link will be added. Prior-work paragraph marked TO CONFIRM BY OWNER; the arXiv 2504.07844 credit is limited to the two-stage idea, per the coordinator's correction.
- `scripts/gates/impact-qollab-run.py`: the acceptance gate (below).

## What was verified (command → exit → artifact)

All local, macOS, venv outside the repo (`/tmp/qollab-qaoa-venv`, Python 3.14.6, Qiskit 2.5.2, SciPy 1.18.1). Details: `evidence/impact-qollab/README.md`.

- `cd impact-qollab && /tmp/qollab-qaoa-venv/bin/python -c "from main import main; main()"` → 0 → `evidence/impact-qollab/run-local.txt`. Re-run diffed: identical except timings.
- `/tmp/qollab-qaoa-venv/bin/python scripts/gates/impact-qollab-run.py` → 0 → `evidence/impact-qollab/gate-run.txt` (`IMPACT-QOLLAB-RUN PASS`). Exactly ONE `backend.run` call per `main()` for 5 configurations, with a backend that raises on a second call; both circuits in that call; optimum equals an independent brute force; energies and gaps recomputed; XY samples all feasible.
- `/tmp/qollab-qaoa-venv/bin/python evidence/impact-qollab/sabotage.py` → 0 → `evidence/impact-qollab/gate-sabotage.txt` (7 of 7 sabotages caught).
- `cd impact-qollab && /tmp/qollab-qaoa-venv/bin/python ../evidence/impact-qollab/seed_sweep.py` → 0 → `evidence/impact-qollab/seed-sweep.txt`.
- `node evidence/impact-qollab/pyodide-probe.mjs <pyodide@314.0.7> impact-qollab` → 0 → `evidence/impact-qollab/pyodide-probe.txt`: under Pyodide 314.0.7 (Python 3.14.2, SciPy 1.18.0) the classical half runs, and **`scipy.optimize.milp` (HiGHS) works**, certified gap 0.
- `node scripts/gates/qollab-submission.mjs impact-qollab` → 1 → `evidence/impact-qollab/qollab-submission-gate.txt`: the only failure is "README.md has no YouTube demo video link". `--selftest` → PASS.

## What is NOT verified

- **Not run on Qollab.** No Run on Qollab press, no Pyodide run of the Qiskit half: stock Pyodide cannot install Qiskit 2.x (`micropip` finds no wasm wheel; Qollab ships its own build). Browser runtime is therefore unknown; locally it is 1.1 s, with about 720 `Statevector` evaluations that will be slower in WASM.
- **Not run on IonQ.** Neither the remote simulators nor hardware (free status unresolved signed out). The one-job property is proven only with a stand-in backend. Unverified: that `qiskit-ionq` accepts the 2-circuit list in one job on Qollab, that `get_counts(i)` indexes it, and how many feasible XY shots survive the noise model.
- `js.sendFile` path not exercised (guarded so it cannot fail a finished run).
- KaTeX and table rendering of the README on Qollab not previewed.
- The owner has not confirmed the prior-work paragraph.

## Null results and findings worth keeping

- The first version of the gate missed 2 of 7 sabotages: the SYNTHETIC check matched the JSON label rather than the console warning, and the gap check was vacuous because every row had gap 0. Fixed by checking the warning text and adding a 16-shot run where the X mixer misses, plus a check that at least one non-zero gap was graded.
- "Best sample is the optimum" is not evidence at this size (1024 random 2-subsets of 15 almost surely contain it). P(optimum) against 1/C(n,k) is the honest metric, and the page says so.
- The QUBO's equal-weight optimum (IWM+TLT) is not the best portfolio after SLSQP sizing (DIA+TLT, objective 0.004339 vs 0.005052): a formulation effect that every solver shares, printed in the console.
- XY P(optimum) varies widely across seeds (0.034 to 0.497 at n=6, k=2): the angle search, not the circuit, is the weak link.

## Open questions

1. Owner: confirm the prior-work paragraph (QC-TRADE written 2026-10-10 in the window, with AI assistance).
2. Owner / quality lane: press Run on Qollab, Built-in simulator, defaults, and compare with `run-local.txt` (selections, energies and shot statistics should match; times will not).
3. Owner: if IonQ simulators show Free when signed in, run once on IonQ Forte 1 or Aria and record the feasible XY share.
4. Upload from a clean checkout (or the GitHub zip): the local folder may hold ignored `__pycache__/` directories that a folder upload would include.

## Related

- [[Research/impact-qc-trade-fit]] · [[Research/qollab-platform-and-submission]] · [[Design/impact-qc-trade-spec]]
