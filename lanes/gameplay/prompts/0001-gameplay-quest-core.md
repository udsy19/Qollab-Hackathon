# Rules for every worker agent (read before your brief)

You are a Claude Code agent directed by the supervisor of lane `gameplay`. Read `/Users/udsy/agent-org/lanes/gameplay/context.md`
first: the product, the owner's rulings and what has NOT worked.

- **HEADLESS.** Your process exits the moment you end your turn. Run every command in the FOREGROUND and
  wait for it. Never use run_in_background or Monitor, and never end your turn "to wait". Write your report
  before you stop.
- **VAULT FIRST (mandatory).** Before you design or build, search the vault for what is already known about
  your goal. Start at `vault/AGENTS.md` (routing), `vault/Index.md` (decided, measured, tried, rejected) and
  `vault/Map-code.md`, then the relevant `Design/`, `Research/`, `Reports/`, `Decisions/` and `Sessions/`
  notes.
  - Your report OPENS with a **Vault check**: notes read (paths), what was already known, what you reused,
    and what is wrong or stale.
  - Before you finish, write your durable findings back: measured findings to `vault/Reports/`, findings
    about the outside world (cited) to `vault/Research/`. Where each kind of finding goes:
    `vault/Design/lanes-and-supervisors.md` § Where research findings go.
  - **Never edit or commit the generated files**: the folder hubs (`vault/**/README.md`), `vault/Map.md`
    and `vault/Index.md` (its PROMOTED block is the overseer's). The loop regenerates the hubs after every
    MERGE and LAND; branches that commit their own hub output only conflict with each other. Run
    `node scripts/vault-hubs.mjs --check` if you want to see that your note will be linked.
  - Before writing any new symbol: `vault/Index.md`, then `node scripts/where.mjs <name> --branches`,
    then `git grep` (`.claude/rules/no-bloat.md`). Delete what your change supersedes.
  - Rebuilding what the vault records as built, tried or rejected, without saying why, is a failed task.
- **GOAL, not tests.** Derive the checks you need from your goal. Prove results through the REAL product
  (screenshots, drawings, short videos; your own port, never a shared one). Never weaken or delete a test.
  If a test is wrong, prove it and replace it.
- **Your worktree and branch are your own.** Commit small and often, and end messages with the project's
  attribution trailer.
  - Never push or merge to main yourself.
  - Never force-push.
  - Never run `git config` against the shared repo (all worktrees share one `.git/config`).
  - Tests that commit must use a throw-away repo.
  - Do not edit protected paths (`vault/Plan.md`, `vault/Roadmap.md`, `vault/Decisions/`,
    `.claude/rules/`, and the owner's vision docs `ECHO_MASTER_VISION.md`, `ROADMAP_48_HOURS.md`, `QOLLAB_DEPLOYMENT.md`, `CLAUDE_CODE_PROMPTS.md`); a hook refuses it and a landing gate re-checks it. To change one, file
    `node scripts/propose.mjs --row <id> --kind … --why "…"` and say so in your report.
  - No auto-memory: no `memory:` frontmatter, no `.claude/agent-memory/` (per-branch copies conflict).
- **Builds.** Use your own build dir (already set in your env). Heavy builds go through the machine-wide
  queue (it is on your PATH). Build only what you need.
- **Sub-agents.** You may launch your own sub-agents (the Agent tool) for parallel research, review or
  exploration. Give each a goal-framed brief, and merge their findings into YOUR report. You are
  accountable for them. Their only channel is the Agent tool's prompt and return value; they do not
  write the vault. If your Claude Code version does not allow a sub-agent to spawn further agents, do
  all the fan-out yourself.
- **Images the supervisor should see** go in `/Users/udsy/agent-org/lanes/gameplay/renders/<your agent name>/` (PNG, descriptive
  names). It sees only images newer than its last consult (at most 12, shared with the owner's reference
  images in `renders/owner/`), so write the ones that matter last and don't re-save old ones.
- **Never print or commit secrets.**
- **CHECKPOINT REPORT.** You have a fixed time budget. Write your report file within the first 25 minutes, then
  update it at least every 45 minutes (your budget is 2 h). Each update covers state, commits, evidence and next. The final version
  replaces it. Never let more than 45 minutes of findings exist only in your head.
- **REPORT** (to the path at the end of your brief). The supervisor sees its `## TL;DR`, its first ~2k
  characters and its last ~3k, so the shape matters:
  - `## TL;DR` FIRST, at most 10 lines: outcome, evidence paths, what you recommend;
  - Vault check;
  - what you found;
  - what you changed (commits);
  - evidence paths;
  - what you did NOT do or could not verify;
  - `## Questions for the owner` — anything the vision docs do not settle (owner rule: ask, never assume);
  - what the supervisor should do next (LAST, so it is in the tail the supervisor reads).

- **Lane ownership.** You edit only this lane's files: gameplay: `echo/game/` (not `audio.js`), `echo/scene/` (not lighting/rain/props/buildings/effects). Anything else is a request in your report.


# YOUR BRIEF (supervisor, consult 1)

You are agent `gameplay-quest-core` in worktree `/Users/udsy/agent-org/lanes/gameplay/wt/gameplay-quest-core` on branch `lane/gameplay/gameplay-quest-core`.

**GOAL.** The player's progress through ECHO is driven by one deterministic quest state machine. It cannot be skipped, cannot be replayed into a broken state, and it resets cleanly. When the player presses E at the booth, the relay or the rooftop socket, the right thing happens exactly once. Pressing it again or out of order does nothing harmful. Restart returns everything to TITLE.

**VISION.** ECHO: ONE OF ONE, vision §3.4, §9.1–§9.5 and §8.4. §9 is normative: read it in full. It is a teaching game. Physics truth (story token consumed once at TELEPORT_COMMITTED) depends on this machine being idempotent.

**WHAT WE ARE BUILDING.** The Qollab-native game in `echo/`. You build the logic core that the 3D world (a parallel worker, `gameplay-world-controller`) and the UI (the story-ui lane) both drive. You also build a dev-only harness kit outside `echo/` so the graybox can be played before the quantum lane lands.

**WHAT HAS NOT WORKED.** Nothing yet on ECHO (fresh start). Org-wide failures to avoid: optimising against a test suite instead of the product, and building behind flags nobody switches on. Also avoid a "missionStep=9" integer counter, which §9.1 forbids.

**Vault notes to read first:**
- `vault/AGENTS.md`, `vault/Index.md`, `vault/Map-code.md`
- `vault/Research/qollab-platform-and-submission.md` (runtime facts: no storage, `three` by name, `<script>` doesn't run)
- `vault/Design/lanes-and-supervisors.md`
- `/Users/udsy/agent-org/lanes/gameplay/context.md`
- `.claude/rules/lane-ownership.md`

**Deliverables (frozen API: the world worker codes against it, so do not change names):**
1. `echo/game/eventBus.js`: `createEventBus()` returns `{ on(type, fn) → offFn, emit(type, payload) }`. Small, synchronous, and a throwing listener must not break others.
2. `echo/game/state.js`:
   - Exports `QUEST_STATES`, `TRANSITIONS` and `createQuestMachine(bus)`. The machine returns `{ get state(), send(event) → {ok, state, reason}, can(event), reset() }`.
   - It covers every state in §9.1. It adds `BOOT —BOOTED→ TITLE`, a back path `DECLASSIFIED/CREDITS → TITLE` via `RESTART` or `reset()`, and `DECLASSIFIED ↔ CREDITS` so the ending can show both.
   - On success it emits `quest:transition {from,to,event}` and `quest:enter:<STATE>`.
   - An invalid or repeated event returns `ok:false` and emits nothing. `reset()` emits `quest:reset` and returns to TITLE.
   - Also export `TELEPORT_COMMITTED` one-shot protection: a second `COMMIT_TRANSFER` is impossible by construction. Show that it is.
3. `echo/game/objectives.js`, only if no data-driven objective text exists anywhere (`node scripts/where.mjs objectives --branches`; story-ui owns `echo/data/`). If story-ui has nothing yet, keep a minimal state→objective-id map and flag the seam in your report.
4. `dev/gameplay/fakeQuantum.js`, which lives outside `echo/` because it is dev-only and must never ship.
   - It implements the §8.4 `QuantumEngine` interface (`cloneTest`, `bellSignalling`, `teleportDryRun`, `verifySelectedBackendOnce`).
   - It returns schema-valid `ExperimentResult` objects with `engine: 'documented_preview'`.
   - The values must be physically correct for the documented cases: basis states clone, |+> fails, receiver marginal 0.5/0.5 for I/X/Z, teleport fidelity 1 only with X iff m1=1 and Z iff m0=1.
   - Add a small async delay plus an injectable failure, so the "honest retry/error" path can be exercised.
5. `dev/gameplay/devTerminal.js`: a throwaway DOM terminal the harness uses to drive the per-mission events (§9.2) by calling the fake adapter. It must only advance on a result, never on a bare click.
6. Checks you derive yourself, runnable with `node` and no npm (plain `node:test` or `node:assert` in `dev/gameplay/tests/`):
   - A full legal walk from BOOT to CREDITS.
   - Every illegal (state, event) pair rejected, enumerated from `TRANSITIONS`, not a hand list.
   - Idempotency and reset.
   - Write them first and watch them fail.
   - Then sabotage: remove one transition and add a skip edge, and report which check went red.

**How I will judge:**
- I read the code and run your checks myself.
- The enumeration is derived, not typed.
- The sabotage round is reported, including any sabotage that did not go red.
- The fake adapter's numbers match §7 physics.
- No storage or POST.
- Nothing dev-only is inside `echo/`.

**Report** to `/Users/udsy/agent-org/lanes/gameplay/reports/`:
- Open with a Vault check.
- Then TL;DR, files, commands + exit codes, the sabotage table, seams/requests for other lanes, and `## Questions for the owner`.
- Write a short `vault/Reports/` note on the state machine contract.
- Checkpoint report within 1 h. Commit small. Your port, if you serve anything: 8611.

**Write your report to `/Users/udsy/agent-org/lanes/gameplay/reports/0001-gameplay-quest-core.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/gameplay/renders/gameplay-quest-core/` (PNG; only images newer than its last consult are shown to it).
