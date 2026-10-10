---
type: dashboard
status: current
date: 2026-10-09
updated: 2026-10-09
---

# Qollab-Hackathon — mission control

> [!abstract] The goal
> **Three Qiskit projects, one per hackathon track (Quantum Impact, Quantum Playground, Quantum Unlocked), each runnable on Qollab's free simulators including IonQ's, and each good enough to win its track.** Full statement: [[Vision]]. Delivery tracker: [[Roadmap]]. Ordered work:
> [[Plan]]. The mission in force: [[Missions/qollab-ionq-hackathon-2026]]. What governs the machine that builds it —
> and what only looks like it does: [[Architecture]].
>
> Every note in this vault, by folder: **[[Map]] · [[AGENTS|agent contract — read first]] ·
> [[SUPERVISOR|supervisor contract]] · [[Map-code|code map]] · [[Index|index of what's been
> decided]] · [[Design/lanes-and-supervisors|how the lanes run]] · [[CLAUDE|the vault contract]]**
> — and a README in each folder saying what it is for.

## NOW — 2026-10-09

*Rewrite this block whenever the facts change, in the owner's words where possible. Replace, do
not append: superseded NOW text goes to a report under `Reports/`, linked from here.*

**How the work runs:** see [[Design/lanes-and-supervisors]].

**The bar:** Each project runs end-to-end on Qollab's free simulators (including IonQ's) with no sign-in friction, is MIT-licensed and published with a clear project page, has a 2-3 min demo video at a public link, and would score at the top of all four judging traits (novelty, technical execution, impact, documentation).

| track | state |
|---|---|
| Quantum Impact | vision given (2026-10-10): QC-TRADE, imported to `impact/`; gaps to Qollab in [[Research/impact-qc-trade-fit]] (no Qiskit yet, Alpaca can't run on Qollab, licensed data can't be bundled) |
| Quantum Playground | waiting on the owner's product vision |
| Quantum Unlocked | waiting on the owner's product vision |
| repo requirements | done: MIT, attribution, `templates/qollab-project/`, `scripts/gates/qollab-submission.mjs` on the board |

**The org is paused (2026-10-10).** The five setup lanes were stopped and their branches archived to `/Users/udsy/agent-org/archive/lane-branches-2026-10-10.bundle`; GitHub holds only `main` and `backup/lane-state`. Once the owner gives the vision, research agents start, then the lanes are re-cut for three tracks.

## Next 3 moves

- [ ] The owner gives the product vision for the three tracks (Plan O1)
- [ ] Research agents, one sweep per track, from that vision
- [ ] Re-cut the lanes for three tracks and restart them

## Blockers

- *Only what a human must do (a login, a spend decision, a ruling). Each names who unblocks it.*

## Lines in flight

The live lines are declared in [[Reports/audits/SESSION-REGISTRY]]; lane state lives in the
org root (see [[Design/lanes-and-supervisors]]).

## Recent sessions

![[Sessions.base#Recent]]

## Design docs by status

![[Design.base#By status]]

## Active missions

![[Missions.base#Active]]

## Where things are

- **Decisions**: `Decisions/` · **Design specs**: `Design/` · **Missions**: `Missions/`
- **Reports & audits**: `Reports/` (the session registry: [[Reports/audits/SESSION-REGISTRY]])
- **Research** (teardowns, library evaluations, captures): `Research/`
- **Evidence** (NOT in the vault): `evidence/` at the repo root, linked by path
- **Rules Claude loads**: `.claude/rules/` — gate-independence, no-bloat, goals-not-tests,
  vault-first, evidence-and-honesty, protected-paths
- **The org's own board**: `bash scripts/gates/org-board.sh`
