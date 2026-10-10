---
type: session
date: 2026-10-09
line: main (setup/agent-org)
model: claude-opus-5-5 (overseer)
outcome: in-progress
---

# 2026-10-09 — agent-org-setup

## Goal
Install the supervised agent organisation for the Qollab x IonQ hackathon (build window Oct 9 19:00 ET → Oct 11 19:00 ET), so lanes can pitch, build and ship two projects. Serves the first NOW item on [[Home]].

## Vault check
Fresh repo (empty folder, empty public GitHub remote `udsy19/Qollab-Hackathon`). No prior notes; nothing to reuse. Qiskit is not installed on the host yet (workers set up a venv).

## Interview (owner's answers, verbatim)
- Project: "Qollab-Hackathon"
- Runtime: "Local (Recommended)"
- Supervisor: "Claude Opus 5.5"
- Workers: "Opus default + Sonnet"
- Vision: the owner pasted the Qollab x IonQ hackathon brief (rules: Qiskit on Qollab free simulators incl. IonQ's; MIT; published + runnable on Qollab with a project page; built in the window, existing code disclosed; 2–3 min public demo video; judged on novelty & creativity, technical execution, impact potential, documentation quality; submissions close Oct 11 19:00 ET).
- Lanes: "core, ux, quality, deliverables"
- Remote: "https://github.com/udsy19/Qollab-Hackathon.git"
- Themes: "we are doing 1, and 2" → Quantum Playground and Quantum Unlocked (core split into lanes `playground` and `unlocked`; ideas to be pitched by the lanes).
- Deploy: "No, Qollab is manual"
- Rules: "Free simulators only"
- What has not worked: nothing yet (first build).
- Summary shown (lanes table, models, runtime, rules) → owner: "Yes, set it up".

## What changed
- `330d145` — repo layer installed by `init-repo.mjs` (vault, rules, hooks, gates, role cards); `.claude/rules/hackathon-eligibility.md` for the owner's rulings; `CLAUDE.md`; loop-guard fixed to match UTC log stamps (it missed every dispatch after UTC midnight west of UTC).
- `7fdbee9` — `.claude/loop-prompts/org-tracker.md`, the overseer's `/loop` prompt.
- Org layer at `/Users/udsy/agent-org`: `org.json` (Claude opus-5-5 supervisor; opus default + sonnet workers; 4 h agent timeout), five lanes created and started (`lane-<name>` tmux), `gitsync` tmux, hourly gc + state-snapshot cron. `flock` installed via brew; the event feed runs under Homebrew bash 5 (macOS bash 3.2 lacks `declare -A`).
- Kit fix: `lanes.sh new` could not find its templates when run from the ORG_ROOT copy; bootstrap now copies `templates/lane` into ORG_ROOT.

## Verified
- `bash scripts/gates/org-board.sh` → `ORG-BOARD PASS — 16 of 17 row(s) green, 1 skipped` (code map: no graph yet).
- `plan-ownership.mjs --since main` PASS; `sprawl.mjs --base main` PASS on the setup commit.
- Every lane logged `=== CONSULT 1` at 2026-10-10 00:49 UTC and dispatched workers (7 running: 2+2+1+1+1).
- Worker auth probe: OK. `state-snapshot.sh` pushed `backup/lane-state`.
- Lane branches pushed to origin (13 refs) — by hand; the gitsync loop's own push is still being verified.
- Still pending: the first worker checkpoint report opening with a Vault check.

## Decisions taken / proposed
- Taken (inside my mandate): core lane split into two priority lanes, one per theme; ux does not land on main; setup fast-forwarded onto `main` (lane integration branches are cut from main, and main deploys nothing); agent timeout 4 h instead of 8 h for a 48 h build.

## Open questions for the owner
- Which of the 3 pitched ideas per theme to build (arrives via ASK_OWNER).

## Next
- Lanes start; first consult of playground/unlocked pitches ideas to the owner.
