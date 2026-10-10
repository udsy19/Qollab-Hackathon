# Track 1 integration audit

How each agent's work was recovered, checked and merged into `main`, with the commands and exit codes actually run. Recovery point before any integration: local tag `checkpoint/pre-integration-2026-10-10` (on `0601d77`). Nothing was pushed, no IonQ job was sent, no Alpaca call was made, no order exists anywhere in the code.

Environments: Python 3.13.0 venv with qiskit 2.5.2 (Qollab project checks); Python 3.13.0 venv with `impact/requirements.txt` (QC-TRADE tests). Host `python3` is 3.14.6.

## Baseline before integration

| check | command | result |
|---|---|---|
| original QC-TRADE tests on `main` (`0601d77`) | `cd impact && python -m pytest -q` (copy via `git archive main impact`) | `28 passed in 15.31s`, exit 0 |

## qollab-qaoa → `impact-qollab/` (Plan row 3)

Branch `worktree-agent-a123cc5cc245fd62f`, last commit `a26edf7`, worktree clean at merge. Merged with `git merge --no-ff --no-commit`, generated vault pages regenerated, committed as `d385242`.

**Independent checks** (my own, not the agent's), run on the merged tree:

| property | how checked | result |
|---|---|---|
| Dicke-state preparation (XY initial state) is the uniform superposition of k-hot strings | statevector for (n,k) = (4,2), (6,2), (6,3), (5,1), (6,5) | pass, all five |
| `_ccry` is a correct doubly controlled RY | algebra: CCX·RY(−θ/2)·CCX·RY(θ/2) = X·RY(−θ/2)·X·RY(θ/2) = RY(θ) on controls 11, identity otherwise; exercised by the Dicke check | correct |
| QUBO → Ising mapping (x = (1−z)/2; h_i = −S_ii/2 − Σ_{j≠i} S_ij/2; J_ij = S_ij/2) and the cost layer | the cost layer's unitary diagonal equals exp(−iγE(x)) up to a global phase on a random 5-variable QUBO | pass |
| penalty λ(Σx−k)² without its constant | algebra: λ·11ᵀ − 2kλ·I on the matrix | correct |
| XY mixer preserves cardinality | 3 layers, random angles: probability outside k-hot = 2.5e−34 | pass |
| the check can fail | control: one X-mixer layer leaves 0.68 of the probability outside k-hot | fails as it must |
| equal objectives across solvers | all solvers score the same `E(y) = y'Qy`; the X-mixer QAOA optimises the penalised QUBO but is scored on the unpenalised one, feasible samples only; exact enumeration is ground truth | consistent (see below) |
| end-to-end run, deterministic example vs exact optimum | `cd impact-qollab && python -c "from main import main; main()"` | exit 0, 1.2 s, "Jobs sent to the backend: 1"; every solver selects IWM+TLT = the exact optimum (gap 0) |

Commands and outputs: `evidence/integration/verify_qaoa_circuits.py` → `VERIFY-QAOA-CIRCUITS PASS` (`evidence/integration/verify_qaoa_circuits.fd5261f.txt`; re-run on the merge, same result); run log `evidence/integration/impact-qollab-run.fd5261f.txt`.

**The agent's own gates, re-run on the merge:** `python scripts/gates/impact-qollab-run.py` → `IMPACT-QOLLAB-RUN PASS` (one `backend.run` per run against a stand-in backend that raises on a second call; every energy and gap recomputed). `node scripts/gates/qollab-submission.mjs impact-qollab` → exit 1, failing only "README.md has no YouTube demo video link" (the video does not exist yet; this row stays red on the org board until the owner records it).

**Formulation notes:** both QAOA variants and all classical solvers share one QUBO. The X mixer adds λ(Σx−k)² with λ = 4·Σ|Q| (QC-TRADE's choice, which makes the feasible optimum the ground state); the XY mixer enforces cardinality exactly, by construction. Stage A (QUBO) scores equal weights, so the QUBO optimum (IWM+TLT) need not be the best portfolio after stage-B sizing (DIA+TLT is, on the default instance); the page states this as a property shared by every solver.

**Not verified:** the Qiskit half has never run under Pyodide (stock Pyodide cannot `micropip install` Qiskit 2.x; Qollab ships its own build), so the run on Qollab itself is unverified; no IonQ run; whether `qiskit-ionq` accepts two circuits in one job.

## research-audit → `impact/` backtest side (Plan row 4)

Branch `worktree-agent-a555f850f32975121`, last commit `e771796`, worktree clean. Merged as `464a8dd`; the only conflicts were the generated vault pages (`Index.md`, `Map.md`, `Reports/README.md`), resolved by regenerating them, not by hand.

| check | command | result |
|---|---|---|
| full QC-TRADE suite on the merged tree (overseer's own run) | `cd impact && python -m pytest -q` | `43 passed in 8.94s`, exit 0 (baseline was 28) |
| the new integrity tests were red before the fixes | agent's log `evidence/impact-research-audit/integrity-red-before-fix.txt` at `45b6c3b` | `15 failed` |
| no look-ahead leak in the original engine | `evidence/impact-research-audit/probe-leak-unmodified.txt` | perturbing future open/close/volume at 3 cut points changed nothing earlier, for 9 classical methods |
| the tests can fail | sabotage rounds, `evidence/impact-research-audit/sabotage-round-2.txt` | 12 of 12 deliberate engine breaks caught |

What changed: a share/cash ledger with a fill log (fills at the next bar's open, sells before buys, buys capped at cash, whole shares by default), four labelled cost scenarios ("MODELED from OHLCV, not observed quotes"), an additive stress grid, an audit gate that requires a positive return under conservative costs, refusal of non-contiguous price panels, $25k default capital. The cost-scenario parameters are the agent's assumptions for liquid ETFs, not calibrated.

Open items in other agents' files (`impact/AUDIT.md` O1–O7) were relayed: O1–O4 to research-solvers while it was still running (the QAOA "gap 0" result at n=6, k=2 is matched by uniform random sampling with the same shots, so it says nothing about the circuit); O5–O7 belong to research-data. Two proposals were filed through `scripts/propose.mjs` (`vault/_log/proposals.jsonl`): #1 challenges row 4's "red before the fix" premise (there was no leak to catch); #2 adds a random-sampling baseline to row 5.

## research-data → `impact/` data pipeline

Branch `worktree-agent-ab34ad640e652b34d`, last commit `4a44651` (it had already merged `main`), worktree clean; merged with no content conflicts.

| check | command | result |
|---|---|---|
| full QC-TRADE suite on the merged tree (overseer's own run, Python 3.13, pandas from `impact/requirements.txt` + pyarrow) | `cd impact && python -m pytest -q -p no:cacheprovider` | `82 passed in 19.74s`, exit 0 |
| the data tests can fail | agent's mutation run, `evidence/impact-research-data/sabotage.txt` | 25 of 25 mutations red |
| dry runs touch no network and no keys | `evidence/impact-research-data/dry-run-{smoke,pilot,full}.txt` | exit 0; full mode = 204 symbol-month requests, latest permitted session 2026-10-09 |
| GET-only, no order endpoint | read `impact/qc_trade/alpaca_paper.py`: one `_get_json` path, GET allow-list, no redirects | confirmed |
| no credentials in source or outputs | `git grep` for the key prefixes on `HEAD`; the manifest records `credentials_recorded: false` | none found |

Audit items O5–O7 (relayed to this agent while it ran) are fixed with tests: per-row timezone validation, an explicit configurable session-completeness policy with per-symbol rejection reasons and a selection-bias check, and distinct messages for connection, 401, 403, 429 and 5xx failures.

## research-solvers → `impact/` optimisation side (Plan row 5)

Branch `worktree-agent-af390822910e72793`, last commit `0987166`, worktree clean. It branched before the audit and data merges, so it was merged in a separate temporary worktree (branch `integrate/solvers`) while a real-data backtest ran from the main checkout. Conflicts: `impact/pyproject.toml` (both sides added dependencies; resolved as the union: pyarrow, qiskit 2.5.2, qiskit-aer 0.17.2) and the generated vault pages (regenerated).

| check | command | result |
|---|---|---|
| full QC-TRADE suite on the merged tree (overseer's own run) | `cd impact && python -m pytest -q -p no:cacheprovider` | `136 passed in 16.03s`, exit 0 (28 original + audit/data + 54 solver tests) |
| every module imports after the merge | `python -c "import qc_trade.cli, qc_trade.backtest, qc_trade.benchmark, qc_trade.optimizer, qc_trade.qaoa, qc_trade.scaling, qc_trade.fetch, qc_trade.dataset, qc_trade.audit, qc_trade.demo"` | OK |
| no caller of a deleted function | `grep` for the old NumPy QAOA names | they remain as wrappers over the Qiskit QAOA; no dangling reference |
| the solver tests can fail | agent's sabotage matrix, `evidence/impact-research-solvers/sabotage.log` | 18 of 18 red |
| scaling study | agent's run, `impact/outputs/scaling/` | 537 solves, 0 errors, N = 6..100 |

Equivalence: all solvers optimise the same QUBO; the X-mixer QAOA uses a cardinality penalty instead of the hard constraint, at the smallest weight that provably keeps the same optimum (brute-force tested). Audit items O1–O4 are fixed: every QAOA row carries a uniform random k-hot sampler with the same 1,024 shots and the approximation ratio; one shared enumeration cap; a MILP time-out is recorded, not a crash.

## Real-data runs (overseer)

Keys: the owner's Alpaca PAPER pair, stored outside the repo (`~/.config/qc-trade/alpaca-paper.env`, mode 600), sourced in a subshell only for read-only commands, never printed; `git grep` for the key prefixes on every commit found none. Commands and records: `evidence/integration/alpaca-check-2026-10-10.txt` (SIP and IEX allowed, account ACTIVE, 0 orders), `alpaca-fetch-smoke-2026-10-10.txt`, `alpaca-fetch-full-2026-10-10.txt`. The backtest was pre-registered (`impact/PREREGISTRATION_2026-10-10.md`, commit `249aa15`) before any real-data return was computed. The primary run was refused by the data-quality gate and the threshold was not changed; the pre-registered no-DIA run and the real-data solver benchmark ran to completion (`impact/outputs/real_full_noDIA/`, `impact/outputs/real_bench_noDIA/`). Raw prices (`fills.csv`, the Parquet cache) are gitignored.

## Final checks on `main` (`67826d2`)

`evidence/integration/final-checks-67826d2.txt`: 136 tests passed; compile and imports OK; exact = MILP on 20/20 seeded instances; Qollab project run exit 0 with 1 job, `VERIFY-QAOA-CIRCUITS PASS`, `IMPACT-QOLLAB-RUN PASS`; backtest integrity tests 16 passed; demo runs; scaling summary reproduced from the committed trials; Qollab submission gate fails only on the missing video link.

## Merge record

| merge | commit | from |
|---|---|---|
| qollab-qaoa | `d385242` | `worktree-agent-a123cc5cc245fd62f` @ `a26edf7` |
| research-audit | `464a8dd` | `worktree-agent-a555f850f32975121` @ `e771796` |
| research-data | `c5fe465` | `worktree-agent-ab34ad640e652b34d` @ `4a44651` |
| research-solvers | `2b6e517` on `integrate/solvers`, then `c85d627` into `main` | `worktree-agent-af390822910e72793` @ `0987166` |
| real-data results | `efe94b3`, `67826d2` | overseer runs |

Agent worktrees and branches are left in place (not deleted) for recovery; the local tag `checkpoint/pre-integration-2026-10-10` marks the state before integration. Slip recorded earlier: one commit accidentally included the agent worktrees as gitlinks and was pushed; it was fixed forward without a force-push (`.claude/worktrees/` is now gitignored).
