---
type: session
date: 2026-10-09
line: main
model: claude-opus-5-5 (overseer)
outcome: done
---

# 2026-10-09 — three-tracks

## Goal
Reshape the vault for the owner's ruling "we are doing all 3 tracks" (Quantum Impact, Quantum Playground, Quantum Unlocked), after pausing the org and making the repo meet the hackathon requirements. Serves the NOW item on [[Home]].

## Vault check
Read [[Vision]], [[Roadmap]], [[Plan]], [[Missions/qollab-ionq-hackathon-2026]], [[Design/lanes-and-supervisors]] and `vault/Research/qollab-platform-and-submission.md` (landed by the deliverables lane before the pause). All still said two projects; every one is updated.

## What the owner said (verbatim)
- "why do we have 14 branches bro, fix that / i have not even given you the roadmp and vision yet / once i do, we will spawn research agents for everything"
- "ill give you the product vision in a bit, but make the repo adhere to the requriements"
- "we are doing all 3 tracks, so make the vault accordinf to that"

## What changed
- Org paused: all five lanes, their workers and git-sync stopped; work in progress committed; 13 lane branches bundled to `/Users/udsy/agent-org/archive/lane-branches-2026-10-10.bundle`, then deleted locally and on GitHub. Lane branches now stay local (`org.json` sync `branch_globs: []`, `push_lane_branches: false`).
- `c61107e`: MIT `LICENSE`, root `README.md` (requirements table), `templates/qollab-project/`, `scripts/gates/qollab-submission.mjs` on the org board, eligibility rule extended.
- This change: Vision, Mission, Roadmap (Tracks B–E: one per hackathon track plus submission), Plan (owner blocks O1 vision, O2 IonQ credits), Home, lanes design note, `CLAUDE.md`, `README.md` and the template, all for three tracks.

## Verified
- `node scripts/gates/qollab-submission.mjs --selftest` → `QOLLAB-SUBMISSION SELFTEST PASS` (13 broken fixtures caught); the template's `main.py` ran locally (`{'11': 531, '00': 493}`, qiskit 2.5.2). Not yet run on Qollab.

## Open questions for the owner
- O1: the product vision for each track.
- O2: IonQ simulator credits when signed in, and whether to spend them.

## Next
- When the vision arrives: write it into [[Vision]] in the owner's words, launch research agents per track, then re-cut and restart the lanes.
