---
type: roadmap
status: current
date: 2026-10-09
updated: 2026-10-09
owner: supervisor
---

# Qollab-Hackathon — Roadmap & Delivery Checklist

**Living document.** The canonical "what does done mean, per track" tracker. Supervisor-owned
(a subagent proposes with `scripts/propose.mjs`). Update it in the *same change* as the work:
tick `[x]` when done AND verified, mark `[~]` partial with a note, leave `[ ]` for not-started.
Keep it honest — a half-working feature stays unchecked with a note. The ordered work that
delivers these items is [[Plan]]; every Plan row cites the Roadmap item it serves by its QUOTED
WORDS, which `scripts/gates/plan-integrity.mjs` resolves against this file.

North star: **Three Qiskit projects, one per hackathon track (Quantum Impact, Quantum Playground, Quantum Unlocked), each runnable on Qollab's free simulators including IonQ's, and each good enough to win its track.** Full vision: [[Vision]].

Legend: `[x]` done & verified · `[~]` partial / needs more · `[ ]` planned · `⏸` parked (deliberate).

## Track A — The organisation itself

- [ ] Bootstrap: the agent organisation is installed and its board is green
- [ ] Every lane named at set-up has produced one result the owner judged by looking

## Track B — Quantum Impact (real-world problems with quantum + classical computing)

- [ ] Impact: product vision given by the owner and the project defined
- [ ] Impact: runs end-to-end on Qollab's built-in simulator and on an IonQ simulator
- [ ] Impact: project page, demo video and `qollab-submission.mjs` green; published on Qollab

## Track C — Quantum Playground (playful, artistic or unexpected)

- [ ] Playground: product vision given by the owner and the project defined
- [ ] Playground: runs end-to-end on Qollab's built-in simulator and on an IonQ simulator
- [ ] Playground: project page, demo video and `qollab-submission.mjs` green; published on Qollab

## Track D — Quantum Unlocked (make the hardest ideas in quantum computing click)

- [ ] Unlocked: product vision given by the owner and the project defined
- [ ] Unlocked: runs end-to-end on Qollab's built-in simulator and on an IonQ simulator
- [ ] Unlocked: project page, demo video and `qollab-submission.mjs` green; published on Qollab

## Track E — Submission (deadline 2026-10-11 19:00 ET)

- [x] Repo meets the hackathon requirements: MIT licence, attribution, project template, `qollab-submission.mjs` on the board
- [ ] All three projects submitted by the captain, each under its own track, before 2026-10-11 19:00 ET

## Known bugs / debt

- *One line each, with the evidence path that shows it.*

## Plan of record — the landing ticks

**Ordered work: [[Plan]].**

> **This subsection lives at the END of the file ON PURPOSE, and a lander appends its tick as the
> LAST line.** A tick inserted near the top pushes every line below it down and ages every
> `Roadmap.md:<line>` citation in [[Plan]]. From the end of the file, a tick moves nothing.
> After any other edit to this file, run `node scripts/gates/plan-integrity.mjs --relocate`, then
> the plain gate: `--relocate` re-derives every citation's line from its quoted words and refuses
> BY NAME, writing nothing, when a quote matches no line or two. Three rows of plan-integrity grade
> this position: this heading is the LAST heading, at least one tick lives under it, and no
> `- [x] … (landed …)` line lives above it.

- [x] Agent organisation installed from the agent-org kit (landed 2026-10-09)
