---
type: mission
status: current
date: 2026-10-09
updated: 2026-10-09
owner: supervisor
accepted-by: owner
accepted: 2026-10-09
state: running
---

# Mission — Ship two winning Qiskit projects for the Qollab x IonQ hackathon

## NOW

**Accepted by the owner, 2026-10-09.** This mission is in force: `.claude/settings.json` names it in
`ORG_MISSION`, the SessionStart hook prints this block into every session, and
`scripts/loop-guard.sh` gates on this note's `state:`.

**The goal:** By Oct 11 19:00 ET, publish two MIT-licensed Qiskit projects on Qollab that run on Qollab's free simulators, including IonQ's simulator: one in the Quantum Playground theme (playful, artistic or unexpected) and one in Quantum Unlocked (make the hardest quantum ideas click). Each has a Qollab project page explaining what it does and how to run it, and a 2-3 minute public demo video.

**The bar:** Each project runs end-to-end on Qollab's free simulators (including IonQ's) with no sign-in friction, is MIT-licensed and published with a clear project page, has a 2-3 min demo video at a public link, and would score at the top of all four judging traits (novelty, technical execution, impact, documentation).

**What has NOT worked** (so nobody repeats it): Nothing yet; this is the first build (started 2026-10-09).

**First moves:** Plan rows 1–2 (`node scripts/plan-row.mjs 1`).

*Everything between `## NOW` and `## ---END-NOW` is printed at the start of every session, so keep
it short, current and in the owner's words. Rewrite it; never append history here.*

## ---END-NOW

## Goal

The end state in one paragraph, and the NOW item on [[Home]] it serves.

## Definition of done

*Owner-edited. One row per property, each with the gate or browser check that proves it.*

| # | property that must hold | gate or browser check that proves it | status |
|---|---|---|---|

## Pre-registration

Before any fix: the observation, the hypothesised cause, the gate that will go RED on the unfixed
tree, and what would falsify the hypothesis (see `.claude/rules/gate-independence.md`).

## Lanes

| lane | supervisor | branch | state |
|---|---|---|---|

## Human gates (an agent may NEVER close these)

- *Acceptance of this mission, the owner's verdict on a result, logins and spend.*

## Log

Newest first. One line per iteration: date · what was tried · verdict · evidence path.
