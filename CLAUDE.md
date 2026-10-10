# Qollab-Hackathon

Two Qiskit projects for the Qollab x IonQ hackathon (Quantum Playground + Quantum Unlocked). Hard rules: `.claude/rules/hackathon-eligibility.md`.

## How work is organised (agent-org)

- **Start of every session:** `/session-open` — read `vault/Home.md`, the newest `vault/Sessions/` note
  and the mission in force. The vault is mission control: its contract is `vault/CLAUDE.md`, its routing
  table for every agent is `vault/AGENTS.md`, the supervisor's contract is `vault/SUPERVISOR.md`, and who
  may write what is the authority matrix in `vault/Architecture.md`.
- **Lanes:** work runs in supervised lanes — one supervisor per lane plans and judges, worker agents build,
  workers may use sub-agents. See `vault/Design/lanes-and-supervisors.md`. Org root `/Users/udsy/agent-org` on
  localhost (tmux on the owner's Mac).
- **Rules** (`.claude/rules/`, auto-loaded): gate-independence · no-bloat · goals-not-tests · vault-first ·
  evidence-and-honesty · protected-paths · hackathon-eligibility.
- **Protected (supervisor/owner only, enforced by hook + landing gate):** `vault/Plan.md`,
  `vault/Roadmap.md`, `vault/Decisions/`, `.claude/rules/`. Everyone else: `node scripts/propose.mjs`.
- **Before writing a new symbol:** `vault/Index.md` → `node scripts/where.mjs <name> --branches` →
  `git grep`. Delete what you supersede in the same change.
- **The org's board:** `bash scripts/gates/org-board.sh` (0 green · 1 red · skips named, never passes).
- **End of every session:** `/session-close` — the session note (`vault/Templates/session.md`), Home NOW,
  `node scripts/vault-hubs.mjs` and `python3 scripts/gen-subject-index.py`.
