---
type: dashboard
status: current
date: 2026-10-09
updated: 2026-10-09
---

# Qollab-Hackathon — mission control

> [!abstract] The goal
> **Two Qiskit projects, one Quantum Playground and one Quantum Unlocked, that are runnable on Qollab's IonQ simulator and good enough to win global specialty awards.** Full statement: [[Vision]]. Delivery tracker: [[Roadmap]]. Ordered work:
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

| lane | state |
|---|---|
| — | the lanes declared at set-up; one line each, with the evidence path of its latest result |

## Next 3 moves

- [ ] playground and unlocked lanes each pitch 3 project ideas to the owner (ASK_OWNER); owner picks one per theme
- [ ] …
- [ ] …

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
