# Portfolio Selection by QAOA: A Skeptical Benchmark

Choosing which k of n assets to hold is a combinatorial problem. This project writes it as a QUBO for six liquid ETFs, solves it with QAOA built in Qiskit (a standard X mixer with a cardinality penalty, and a cardinality-preserving XY mixer), and puts both next to four classical solvers on the same instance: exact enumeration, MILP (HiGHS), greedy local search and simulated annealing. For each one it reports the objective, feasibility, gap to the certified optimum and runtime. It asks one question a skeptical quantitative researcher would ask, and it does not claim a quantum advantage: at this size, classical solvers find the optimum in milliseconds.

Demo video: the link will be added here once the video is published.

**The data are synthetic.** The expected returns and covariance are generated from a seeded simulation with hand-chosen volatilities and correlations that look like SPY, QQQ, IWM, DIA, TLT and GLD. They are not market data, and nothing on this page is a market result or investment advice.

## What it shows

Portfolio construction usually ends in a cardinality constraint: hold exactly k names, to keep trading and monitoring costs down. Picking the best k-subset is a binary quadratic problem, the kind QAOA is designed for, so it is a natural place to test QAOA honestly. The pipeline has two stages. Stage A picks the k assets (the QUBO, solved by every solver). Stage B sizes them with a classical constrained optimiser (SLSQP, weights between 3% and 80%, fully invested).

In one run you see: the instance; the QAOA angles being tuned locally; the two QAOA circuits after transpilation (qubits, depth, two-qubit gates); ONE job carrying both circuits; a results table for all six solvers; the stage-B portfolios; and a verdict computed from the table, not written in advance.

## How to run it

1. Open this page in Chrome, Edge, Brave, Opera or Firefox 153+. Safari and iPhone/iPad cannot run Qollab projects.
2. Press **Run on Qollab** (top right). No sign-in is needed for the free local simulators.
3. Under **Run settings**, keep the defaults: `n_assets` 6 (how many ETFs, up to 8), `k` 2 (how many to hold), `reps` 2 (QAOA layers), `shots` 1024 (samples per circuit), `seed` 7 (fixes the random starts, the annealer and the built-in simulator's sampling), `risk_aversion` 6.0.
4. Pick **Built-in simulator (24q)** under *Locally Run Simulators* and press **Run**.
5. Expected: the console prints the instance, the tuning, the circuits, the results table and the verdict. Locally (CPython on a laptop) the whole run takes about 1 second; in the browser expect a few seconds more while packages load. A JSON copy of the results is offered in the console.
6. On IonQ's simulator: run again and pick an IonQ simulator under *Remotely Run Simulators*. The project sends exactly one job per run: both circuits travel in one `backend.run` call. Only press Run there if the dialog shows the simulator as free.

Locally: `pip install -r requirements.txt scipy`, then `python -c "from main import main; main()"` inside this folder.

## Expected output (default settings, built-in simulator)

This is the results table, abridged, from a local run (CPython 3.14, Qiskit 2.5.2, Qiskit's `BasicSimulator`, which is the simulator the built-in option uses). The run is seeded, so a judge's run should show the same selections, energies and shot statistics; the times will differ.

```
  solver                 selection            QUBO E feasible         gap  rel.gap    time ms  notes
  exact enumeration      IWM+TLT             0.00506 yes          0.00000    0.00%        0.1
  MILP (HiGHS)           IWM+TLT             0.00506 yes          0.00000    0.00%        5.5  certified
  greedy + local swap    IWM+TLT             0.00506 yes          0.00000    0.00%        0.1
  simulated annealing    IWM+TLT             0.00506 yes          0.00000    0.00%       12.4
  QAOA X mixer + penalty IWM+TLT             0.00506 60.3%        0.00000    0.00%      442.8  P(optimum) sampled 0.040, ideal 0.040
  QAOA XY mixer          IWM+TLT             0.00506 100.0%       0.00000    0.00%      627.6  P(optimum) sampled 0.141, ideal 0.119
  baseline: a uniformly random k-subset is optimal with probability 1/C(6,2) = 0.067
```

## How it works

The QUBO is the one from QC-TRADE. For a selection vector $y \in \{0,1\}^n$ with $\sum_i y_i = k$, equal weights $1/k$, expected returns $\mu$, covariance $\Sigma$, risk aversion $\gamma$ and a linear trading-cost prior $c$ against previous holdings $p$ (here cash, $p = 0$): $E(y) = -\mu^\top y / k + \tfrac{\gamma}{2k^2}\, y^\top \Sigma y + c\,\lVert y/k - p \rVert_1$. Lower is better. Every solver minimises this same $E$, and every reported gap is $E - E_{\text{exact}}$.

| concept | circuit | effect |
|---|---|---|
| cost layer | `RZ(2γh_i)` on each qubit and `RZZ(2γJ_ij)` on each pair, from $y_i = (1 - z_i)/2$ | phases each bitstring by its QUBO energy |
| X mixer (standard QAOA) | start in $\lvert + \rangle^{\otimes n}$, mix with `RX(2β)` on each qubit; a penalty $\lambda(\sum y - k)^2$ with $\lambda = 4\sum\lvert Q_{ij}\rvert$ is added to the cost | explores all $2^n$ bitstrings; infeasible ones are sampled, counted and discarded |
| XY mixer (cardinality-preserving) | start in the Dicke state $\lvert D(n,k) \rangle$ (Bärtschi and Eidenbenz's deterministic circuit, O(nk) gates), mix with `XXPlusYYGate(2β)` around a ring | only swaps 01 and 10, so the number of selected assets never changes: every ideal sample is feasible |
| angle tuning | Qiskit `Statevector` of the circuit, COBYLA from 3 seeded starts, minimising the exact expected energy | classical simulation on your machine; sends no jobs |
| sampling | both tuned circuits in ONE `backend.run` call | one job per run, as IonQ backends require |

Why one job is enough: QAOA needs many circuit evaluations only while its angles are being searched. Here that search runs on an exact classical simulation in the browser, and the backend is used once, to sample the two tuned circuits. On an ideal simulator the sampled and ideal probabilities agree to within shot noise, which the table lets you check.

How to read the QAOA rows: "best sample is the optimum" is weak evidence at this size, because 1024 random 2-subsets out of 15 would almost surely contain the optimum too. The informative number is **P(optimum)**, the share of shots that land on the optimum, against the 1/C(n,k) a random k-subset achieves.

## Results across seeds (measured locally, not on Qollab)

Seeds 1 to 10, 1024 shots, reps 2, on the same synthetic instance (`evidence/impact-qollab/seed-sweep.txt` in the repository):

| n, k | random k-subset P(opt) | X mixer P(opt) mean [min, max] | X mixer feasible shots | XY mixer P(opt) mean [min, max] | classical solvers at the optimum |
|---|---|---|---|---|---|
| 6, 2 | 0.067 | 0.044 [0.021, 0.071] | 65.8% | 0.221 [0.034, 0.497] | 4 of 4, every seed, mean ≤ 13 ms |
| 6, 3 | 0.050 | 0.047 [0.037, 0.058] | 94.4% | 0.143 [0.045, 0.303] | 4 of 4, every seed, mean ≤ 13 ms |
| 8, 4 | 0.014 | 0.011 [0.002, 0.021] | 87.1% | 0.116 [0.070, 0.144] | 4 of 4, every seed, mean ≤ 13 ms |

What this says, on this instance only: the XY mixer concentrates probability on the optimum well above random guessing (about 3 to 8 times the 1/C(n,k) baseline on average), while the penalised X mixer does no better than a random k-subset once its infeasible shots are counted. The XY result varies a lot between seeds (0.034 to 0.497 at n=6, k=2), which points at the angle search, not the circuit, as the weak link. None of this is faster than enumeration, which is trivial at these sizes.

## What's new here

The category we claim is **a technical extension (comparative benchmarking)**. One frozen portfolio-selection instance runs through two QAOA variants (X mixer with a penalty; a cardinality-preserving XY mixer started from a Dicke state) and four classical solvers, with feasibility, objective, optimality gap and runtime reported for each, and the classical stage-B allocation applied to every answer. The QAOA circuits are new in this project: QC-TRADE simulated QAOA in NumPy, and here it is rebuilt as Qiskit circuits that run on Qollab's backends within IonQ's one-job-per-run rule. We do not claim a novel application context: QAOA for portfolio selection is well known.

## Limitations

- The data are synthetic. Six to eight assets is tiny; exhaustive search is instant at this size, so no runtime comparison here can favour QAOA, and none is claimed.
- QAOA times are classical simulation times of the angle search plus a share of the transpile and job time. They are not quantum hardware runtimes.
- The QUBO scores equal weights; after stage-B sizing, a different support can be better. The console shows this: on the default instance the QUBO optimum (IWM+TLT) is not the best portfolio after sizing (DIA+TLT is), which is a property of the formulation, shared by every solver.
- One instance, one risk aversion, reps up to what you set. The out-of-sample trading questions of QC-TRADE (backtests, costs, statistical tests) are not part of this Qollab project; they live in the repository's `impact/` folder.
- IonQ noise: the results above are ideal-simulator results. We have not run on IonQ's noise-model simulator; expect fewer feasible XY shots there, since noise breaks the Hamming-weight symmetry the XY mixer relies on.

## Make it yours

- **Your own statistics:** put a JSON with the keys `tickers`, `mu`, `cov`, `synthetic` and `label` next to `data/etf_stats_synthetic.json`, and change the `STATS_FILE` string in `main.py` (Qollab loads a data file only when its path is written out as a plain string). Use derived statistics (annualised mean and covariance), not licensed price data.
- **A bigger problem:** raise `n_assets` (up to the number of tickers in the file) and `k`. The built-in simulator allows 24 qubits and IonQ's simulators 25 to 29, but the local angle search simulates $2^n$ amplitudes, so keep n modest in the browser.
- **A better angle search:** `ANGLE_STARTS` and `ANGLE_MAXITER` in `main.py`; `tune_angles` in `qctrade/qaoa.py`.
- **Another mixer or solver:** `build_qaoa` in `qctrade/qaoa.py`, or a function in `qctrade/solvers.py` added to the `run_classical` calls in `main.py`.

Files: `main.py` (the run and the report), `qctrade/instance.py` (the synthetic data and the loader), `qctrade/solvers.py` (the QUBO, the classical solvers, stage-B sizing), `qctrade/qaoa.py` (the Qiskit circuits, angle tuning, decoding), `data/etf_stats_synthetic.json`.

## Built during the hackathon / prior work

TO CONFIRM BY OWNER: the QUBO construction, the classical solvers and the stage-B sizing are vendored, with the maths unchanged, from QC-TRADE (`impact/qc_trade/optimizer.py` in the repository below), a prototype written on 2026-10-10 inside the build window that opened on 2026-10-09 at 19:00 ET, with AI-tool assistance. QC-TRADE's QAOA was a NumPy statevector simulation; the Qiskit circuits, the Dicke-state preparation, the angle tuning, the one-job sampling, the synthetic six-ETF instance, the Pyodide-compatible runner and this page are new in this project. No third-party code or tutorial was forked.

The two-stage structure (a discrete selection step followed by a continuous allocation step) is adapted from Shinde, Zhu, Shen and Gao, "A quantum computing approach to beam angle optimization" (arXiv:2504.07844; Medical Physics, 2025). That paper chooses proton-therapy beam angles: binary variables select angles and continuous variables set spot intensities. We borrow only the idea of splitting a binary choice from a continuous one; we do not reproduce its method or results. The Dicke-state circuit follows Bärtschi and Eidenbenz, "Deterministic preparation of Dicke states" (2019).

AI tools were used to write code and documentation.

## Accessibility

The project's output is plain text in the console: no colour carries meaning, every number is printed with its label, and the results table is fixed-width so it reads the same in any theme and to a screen reader line by line. The run needs only the Run on Qollab button, the Run settings form and the Run button, all reachable by keyboard. The formulas on this page are also stated in words next to them.

## License

MIT (see `LICENSE`). Source: https://github.com/udsy19/Qollab-Hackathon

This effort is supported by Qollab & IonQ
