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
- Repo layer installed by `init-repo.mjs` (vault, rules, hooks, gates, role cards); `.claude/rules/hackathon-eligibility.md` added for the owner's rulings; `CLAUDE.md` created.

## Decisions taken / proposed
- Taken (inside my mandate): core lane split into two priority lanes, one per theme; ux does not land on main.

## Open questions for the owner
- Which of the 3 pitched ideas per theme to build (arrives via ASK_OWNER).

## Next
- Lanes start; first consult of playground/unlocked pitches ideas to the owner.
