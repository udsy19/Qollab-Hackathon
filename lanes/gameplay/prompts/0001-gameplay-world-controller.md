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

You are agent `gameplay-world-controller` in worktree `/Users/udsy/agent-org/lanes/gameplay/wt/gameplay-world-controller` on branch `lane/gameplay/gameplay-world-controller`.

**GOAL.** A judge opens the page, clicks PLAY and walks Rin in third person through a rain-alley street, a connector, a relay chamber and a rooftop. The movement must feel right. They see an "E" prompt only when close to and facing a device, never through a wall. They cannot fall out of the map, and the world visibly reacts when quest events fire: the alley door opens, the relay conduit lights, the rooftop unlocks, the city lights come on at commit.

**VISION.** ECHO: ONE OF ONE. Read vision §3.1 (movement spec), §5.1 (the three spaces and their sizes), §9.3–§9.5 (events, interactables, reset), §10.1 and §10.8 (scene skeleton, controller pseudocode) and §12.1 (perf ≥30 FPS). This is the "playable" in the definition of done. Without it there is no game, only a visualizer, and the owner has explicitly said a visualizer is not acceptable.

**WHAT WE ARE BUILDING.** The Qollab-native Three.js game in `echo/`, delivered as files Qollab runs as-is:
- No bundler or npm. `import * as THREE from 'three'` by name (0.186.1 on Qollab).
- No storage, POST or workers. `<script>` in `index.html` doesn't run.

You own the gameplay side of `echo/game/` and `echo/scene/`. Art (lighting, rain, props, buildings, effects) is another lane. You build primitive graybox geometry with distinct silhouettes per space, and art replaces it later. `echo/main.js` belongs to the platform lane. You export `startGame({ root, quantum, ui })` from `echo/game/app.js` and platform will call it.

**WHAT HAS NOT WORKED.** Nothing yet on ECHO. Avoid:
- A spinning cube or landing page passed off as progress.
- Per-frame heavy state updates.
- Interactions that trigger through walls.
- Judging the wrong artifact. Screenshots must come from the page you just changed: prove the build by reading back a token you changed.

**Parallel worker.** `gameplay-quest-core` is building `echo/game/eventBus.js` and `echo/game/state.js` at the same time. Code against this frozen API:
- `createEventBus()` returns `{on(type, fn) → off, emit(type, payload)}`.
- `createQuestMachine(bus)` returns `{state, send(event) → {ok,state,reason}, can(event), reset()}`.
- It emits `quest:transition {from,to,event}`, `quest:enter:<STATE>` and `quest:reset`.
- States and events are exactly vision §9.1/§9.2, plus `BOOT —BOOTED→ TITLE`.

Until their branch lands (`git fetch` and look for `lane/gameplay/gameplay-quest-core`), use the smallest stand-in. When it lands, merge it into your branch and delete the stand-in in the same change.

**Vault notes to read first:**
- `vault/AGENTS.md`, `vault/Index.md`, `vault/Map-code.md`
- `vault/Research/qollab-platform-and-submission.md`
- `/Users/udsy/agent-org/lanes/gameplay/context.md`
- `.claude/rules/lane-ownership.md` and `.claude/rules/qollab-runtime.md`

**Deliverables:**
1. `echo/scene/renderer.js`, `district.js` (composes the spaces and exports collider boxes + named interactable anchors `copy_booth`, `relay_core`, `classical_socket` and the rooftop terminal), `alley.js`, `relay.js`, `rooftop.js` and `player.js` (a capsule-carrying primitive silhouette).
2. `echo/game/input.js`, `camera.js`, `controller.js` and `interactions.js`:
   - Camera-relative WASD, normalized diagonals, damped acceleration, sprint ≈1.6×, delta-time with clamped steps.
   - Pointer lock only while exploring, released on terminal, pause or blur.
   - Esc pause. AABB collision and bounds, and a camera that is clamped or pulled in near walls.
   - The interaction test is distance (<2.5 m) + facing + line of sight. A device is interactable only when its `requiredQuest` matches the current state.
3. World reactions as idempotent handlers on `quest:enter:*` (§9.3). Doors are gated by state, so you cannot walk to the relay before `RELAY_UNLOCKED`. `quest:reset` restores everything, including player transform and camera (§9.5).
4. `echo/game/app.js` with `startGame`, plus `dev/gameplay/harness.html` (outside `echo/`).
   - The harness uses an importmap that maps `three` to `https://cdn.jsdelivr.net/npm/three@0.186.1/build/three.module.js`, a minimal title/PLAY overlay and a minimal HUD prompt.
   - Terminals are a stub that emits the mission events until the quest-core worker's dev terminal and fake adapter land; then use theirs.
   - Serve it from the worktree root on **port 8612 only**.

**Priority if time runs short:** alley + booth + movement + interaction first (that alone is the one-room fallback), then relay, then rooftop.

**How I will judge:** by looking.
- Screenshots from your port, through the real path: PLAY, walk, prompt visible near the booth, no prompt behind a wall, the door opening after the clone mission, relay and rooftop reachable only in order, the post-commit city reaction, and Restart back to title.
- A short headless video or frame sequence of a walk.
- An FPS readout.
- Each artifact proves its build (a token you changed, read back from the served page).
- Report what you could not verify headlessly, such as real pointer lock, as UNVERIFIED rather than passing.

**Report** to `/Users/udsy/agent-org/lanes/gameplay/reports/`:
- Open with a Vault check.
- Then TL;DR, files, commands + exit codes, screenshot paths under `renders/` or `evidence/gameplay/`, the nulls, requests for the platform lane (the `startGame` contract and how `main.js` should call it), requests for story-ui (UI events you emit), and `## Questions for the owner`.
- Add a `vault/Reports/` note with the controls/collision/interaction contract.
- Checkpoint report within 1 h. Commit small.

**Write your report to `/Users/udsy/agent-org/lanes/gameplay/reports/0001-gameplay-world-controller.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/gameplay/renders/gameplay-world-controller/` (PNG; only images newer than its last consult are shown to it).
