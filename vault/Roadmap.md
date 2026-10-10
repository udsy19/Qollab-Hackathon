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

North star: **Two Qiskit projects, one Quantum Playground and one Quantum Unlocked, that are runnable on Qollab's IonQ simulator and good enough to win global specialty awards.** Full vision: [[Vision]].

Legend: `[x]` done & verified · `[~]` partial / needs more · `[ ]` planned · `⏸` parked (deliberate).

## Track A — The organisation itself

- [ ] Bootstrap: the agent organisation is installed and its board is green
- [ ] Every lane named at set-up has produced one result the owner judged by looking

## Track B — Hackathon submission (deadline 2026-10-11 19:00 ET)

- [ ] Two projects published on Qollab with project pages and public demo videos, both running on the IonQ simulator

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
