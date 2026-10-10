---
type: plan
status: current
date: 2026-10-09
updated: 2026-10-09
owner: supervisor
---

# Plan of record — the ordered work

**The goal** ([[Vision]]): Three Qiskit projects, one per hackathon track (Quantum Impact, Quantum Playground, Quantum Unlocked), each runnable on Qollab's free simulators including IonQ's, and each good enough to win its track. This file is the ONE ordered list of work.
Supervisor-owned: a subagent reads its row with `node scripts/plan-row.mjs <id>` and changes
nothing here — it proposes with `node scripts/propose.mjs`.

**Ordering.** Rows are worked lowest number first unless the "Active order" note below says
otherwise. A row is ONE task an agent can finish and a reviewer can grade; a row that is really
several is decomposed into `N.1 … N.k` BEFORE it is dispatched (`scripts/gates/plan-hierarchy.mjs`:
a parent is not done while a child is open; one level of nesting only).

**A task is ticked by the LANDER, in the same change as the work, with the gate's exit code
quoted** — never by the agent that wrote the code, never off a summary line.

**This plan has its own gate.** `node scripts/gates/plan-integrity.mjs` re-derives everything from
the table's bytes and consumes NOTHING the plan says about itself (not the Status roll-up below).
**The status column is a closed set: `open` · `in-flight:<branch>` · `blocked-on-owner:<Oid>` ·
`done:<sha>`**, and every `<Oid>` must be declared in the "Blocked on the owner" table. Every row
has exactly six cells, none empty, numbered contiguously. **Every row's `serves` cell cites the
[[Roadmap]] item it delivers as `` `Roadmap.md:<line>` ("its own quoted words") ``** — graded on
the quoted words AND on the line number; after a Roadmap edit, `--relocate` re-derives the numbers.
**Every acceptance cell names a gate or test file that exists, or says `gate to write:`** — a gate
written after the fix can only confirm the fix (gate-independence law 3).

## Active order

2026-10-10 17:00 ET (owner): Track 1 Qollab slice first (row 3), the full research platform in parallel (rows 4–6), page and video drafts (row 7). Rows 3–7 run in parallel as overseer-dispatched agents.

## The table

| # | task | serves | owner line | acceptance gate | status |
|---|---|---|---|---|---|
| 1 | Bootstrap the agent organisation from the agent-org kit: vault, rules, hooks, role cards, scripts and the org board | `Roadmap.md:24` ("Bootstrap: the agent organisation is installed and its board is green") | overseer | `bash scripts/gates/org-board.sh` exits 0 on the bootstrap commit (skips named, never counted as passes) | open |
| 1.1 | Fill `vault/Vision.md`, the Home NOW block and the first mission from the owner's interview, in the owner's words | Track A | overseer | `node scripts/loop-state.mjs --check` exits 0 (the mission exists, its `state:` is in the vocabulary, its NOW block is fenced) | open |
| 1.2 | Declare every lane, its goal and its branches in `vault/Design/lanes-and-supervisors.md` | Track A | overseer | `node scripts/gates/vault-reachability.mjs` exits 0 with the note reachable | open |
| 1.3 | Write the set-up session note, recording the interview verbatim, and regenerate the hubs and the Index | Track A | overseer | `node scripts/vault-hubs.mjs --check` and `python3 scripts/gen-subject-index.py --check` both exit 0 | open |
| 2 | Each lane named at set-up delivers one result through the real product, judged by the owner by looking | `Roadmap.md:25` ("Every lane named at set-up has produced one result the owner judged by looking") | each lane supervisor | gate to write: per lane, the owner's verdict on a named evidence path, recorded in the lane's `owner-answers.md` | open |
| 3 | Build `impact-qollab/`: the Qollab Qiskit project — portfolio-selection QUBO solved by X-mixer and XY-mixer QAOA in Qiskit vs exact, greedy, annealing and MILP on the same instance; one IonQ job per run | `Roadmap.md:30` ("Impact: runs end-to-end on Qollab's built-in simulator and on an IonQ simulator") | agent qollab-qaoa | `node scripts/gates/qollab-submission.mjs impact-qollab` exits 0 apart from the video link, plus a local run log in `evidence/impact-qollab/` | in-flight:worktree-qollab-qaoa |
| 4 | Audit `impact/` and fix backtest correctness (leakage, next-bar execution, cash accounting, cost scenarios), test-first | `Roadmap.md:29` ("Impact: product vision given by the owner and the project defined") | agent research-audit | gate to write: the future-price-perturbation test in `impact/tests/`, red before the fix | in-flight:worktree-research-audit |
| 5 | Qiskit QAOA, HiGHS MILP and the solver scaling study (N = 6 to 100) in `impact/qc_trade/` | `Roadmap.md:29` ("Impact: product vision given by the owner and the project defined") | agent research-solvers | gate to write: `impact/tests/test_solvers*.py` (objective equivalence, feasibility, seed determinism) | in-flight:worktree-research-solvers |
| 6 | Read-only Alpaca data pipeline: Parquet cache, manifest, calendar, completeness checks, and one owner-run fetch command | `Roadmap.md:29` ("Impact: product vision given by the owner and the project defined") | agent research-data | gate to write: `impact/tests/test_data*.py` with mocked HTTP | in-flight:worktree-research-data |
| 7 | Impact project-page metadata, demo-video script and rubric self-check | `Roadmap.md:31` ("Impact: project page, demo video and `qollab-submission.mjs` green; published on Qollab") | agent impact-deliverables | gate to write: the owner's review of `docs/impact/page-and-video.md` | open |

*Add product rows below these, numbered contiguously, each citing its Roadmap item.*

## Blocked on the owner

Each is one decision only a human can make. Nothing below is an agent's to perform or simulate
(gate-independence law 9). A row blocked on one carries `blocked-on-owner:O<n>`.

| # | the decision | why it blocks | cited |
|---|---|---|---|
| O1 | The product vision for each of the three tracks (Impact given 2026-10-10: QC-TRADE; Playground and Unlocked pending) | no project can be defined, researched or built without it; agents do not invent it | owner, 2026-10-10: "ill give you the product vision in a bit" |
| O2 | Whether the IonQ simulators cost credits for a signed-in account, and if so whether to spend them | eligibility needs a run on IonQ's simulator; the owner ruled "Free simulators only" and the live dialog says "Credits apply" | `vault/Research/qollab-platform-and-submission.md` § 2 |

## What this plan does NOT include

- *What is deliberately out of scope, and the ruling or reason that put it there.*

## How to work a row

1. Take the row: `node scripts/plan-row.mjs <id>`. Work in your own worktree, on your own branch
   (`lane/<lane>/<slug>`), on your own port.
2. **Write the acceptance gate FIRST and watch it go red** on the unfixed tree.
3. Fix. Then run the **sabotage round** — the assertion, the threshold, and every enabling
   transform under them — against a **disposable** copy, and report the NULLs as loudly as the
   fires (gate-independence law 15).
4. Report → a read-only reviewer **re-derives** the numbers → only on ACCEPT does a lander merge.
5. The lander ticks this row **in the same change**, `done:<sha>`, quoting the gate and its exit
   code, and appends the Roadmap tick at the END of the Roadmap.

## Status roll-up

*Printed, not asserted: re-count it off the `status` column when you change a status, never
increment it by hand. `node scripts/loop-state.mjs` prints the live count.*

| status | rows |
|---|---:|
| `open` | 5 |
| `in-flight:<branch>` | 0 |
| `blocked-on-owner:<Oid>` | 0 |
| `done:<sha>` | 0 |
