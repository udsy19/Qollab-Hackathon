---
type: research
status: current
date: 2026-10-10
updated: 2026-10-10
owner: overseer
tags:
  - impact
  - qc-trade
  - qollab
---

# Impact track: QC-TRADE against Qollab and the hackathon rules

The owner's Track 1 (Quantum Impact) starting point is **QC-TRADE Intraday v2.1**, imported unchanged into `impact/` from `~/Downloads/QC_TRADE_Alpaca_Paper_v21` on 2026-10-10. This note records what it is and what stands between it and an eligible Qollab project. Read from the files only: nothing in it was run, and no network call was made.

## What it is (from `impact/README.md` and the code)

- "A reproducible US stocks/ETFs intraday research prototype for net-of-cost out-of-sample alpha testing and quantum-inspired vs classical combinatorial optimization."
- Asset selection is posed as a **QUBO** (`qc_trade/optimizer.py: qubo_matrix`) from forecast returns `mu`, covariance `cov` and previous holdings, with a cardinality `k`. It is solved by exact enumeration, MILP, greedy swap, simulated annealing, and **QAOA** in two forms: an X-mixer with a cardinality penalty (`qaoa_statevector`) and a cardinality-preserving XY ring mixer (`qaoa_xy_statevector`). Both cap at ≤9 assets.
- A walk-forward intraday backtest (`qc_trade/backtest.py`) with fill costs, a paired block bootstrap against intraday SPY, cost-stress grids, and a pre-registered evidence audit (`qc_trade/audit.py`) that fails every gate on its synthetic demo (`impact/outputs/demo/RESEARCH_AUDIT.md`).
- Alpaca **paper** integration is read-only: GET `/v2/account`, `/v2/clock` and `/v2/stocks/bars`. Keys come only from `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY` in the environment. A credential scan of the import found none in the files.
- Its own stance, which is an asset for the documentation and honesty judging: "No quantum advantage or future profitability has been established", and "QAOA is ideal classical statevector simulation, NOT quantum hardware speedup".
- Size: 32 files, 972 KB (800 KB in `outputs/demo/`), 1,935 lines of Python. Dependencies: numpy, pandas, scipy, requests, exchange-calendars, matplotlib, pytest.

## Provenance (prior work)

The files are dated 2026-10-10 05:11–05:39 (local), inside the build window (opened 2026-10-09 19:00 ET), so this counts as hackathon work. The README speaks of "the author's sandbox", which suggests it was written with an AI assistant: disclose AI-tool use on the project page, as the hackathon terms allow. **Ask the owner** to confirm both points.

## Gaps to an eligible Qollab project

| # | gap | why it matters | source |
|---|---|---|---|
| G1 | **No Qiskit.** QAOA is a hand-written NumPy statevector simulation. | Eligibility: "a Qiskit project". The QAOA circuits must be built in Qiskit and run on Qollab's `backend`. | `qc_trade/optimizer.py:157,209`; `.claude/rules/hackathon-eligibility.md` |
| G2 | **Alpaca cannot be called from Qollab.** It needs API keys, and Qollab forbids keys in published code and allows only CORS GET requests. | The Qollab project must run on bundled data. Alpaca stays an off-Qollab path for data preparation. | `vault/Research/qollab-platform-and-submission.md` § 1 |
| G3 | **Licensed data cannot be bundled.** "never publish licensed price data without permission" (runbook); SIP bars are licensed. | The bundled input must be synthetic, freely redistributable, or a derived statistic (e.g. `mu` and `cov`) whose redistribution the licence allows. **Unverified which.** | `impact/ALPACA_PAPER_RUNBOOK.md`; `impact/.gitignore` |
| G4 | **One job per run on IonQ.** QAOA's parameter search needs many circuit evaluations. | Optimise the angles on the free local simulator, then send ONE final sampling job (or one batched call) to IonQ. | research note § 2 |
| G5 | **Pyodide dependencies.** `requests` is not needed on Qollab (use `pyfetch` or nothing); `exchange-calendars` and `scipy.optimize.milp` availability in Pyodide is **unverified**. | A package without a Pyodide build stops the run. | research note § 1 Libraries |
| G6 | **No `main.py` entry point,** and the package lives in a subfolder. | Qollab needs a top-level `main.py` with a one-line, typed `def main(...)`; whether imports from `qc_trade/` work there is to be checked. | research note § 1 |
| G7 | **Novelty floor.** The project must name its category on the page. | Best fit: "a technical extension (… comparative benchmarking)": QAOA (X and XY mixers) against exact, MILP, annealing and greedy, on the same instances, net of costs, on the IonQ noise models. | hackathon terms |
| G8 | **Size limits.** 100 files and 2 MB per file. | Fine as imported (32 files). Keep bundled data under 2 MB per file. | research note § 1 |

## The Impact story that fits the track

"Solving real-world problems with quantum + classical computing": a classical forecasting and risk pipeline hands a cardinality-constrained portfolio-selection QUBO to QAOA, running in Qiskit on Qollab's simulators and IonQ's noise models. QAOA is benchmarked honestly against classical solvers on the same instances, and the result is judged out of sample, net of costs. That honesty — pre-registered gates, no claimed advantage — is the differentiator, and it serves the documentation trait directly.

## Security note

The runbook records that the paper key pair was disclosed to an assistant. **Rotate it in Alpaca's dashboard** before any real-data run. Keys never enter this repo, the vault or a chat.

## Related
- [[Vision]] · [[Roadmap]] · `vault/Research/qollab-platform-and-submission.md`
