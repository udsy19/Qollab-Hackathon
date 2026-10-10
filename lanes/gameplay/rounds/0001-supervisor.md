=== PLAN ===
**Lane gameplay: plan as of consult 1 (2026-10-09 ~23:20 ET, T+4.5h). G2 is due Sat 2026-10-10 17:00 ET; if we miss it, we cut to the one-room version (vision §13).**

**Goal (plan row 5, our half):** a playable graybox in a desktop browser. A third-person follow camera, WASD + mouse orbit + Shift sprint + E interact + Esc pause, with pointer lock released for UI. Collision and map bounds. Three connected spaces: Rain Alley with the replication booth, then Relay Chamber, then Rooftop, joined by short connectors (vision §5.1). Interaction by distance and facing, blocked through walls. The quest state machine of vision §9.1/§9.2: every state, no invalid skips, idempotent, `resetGame()` per §9.5. World reactions on named events (§9.3). Puzzle results come from a fake adapter that matches the `ExperimentResult` schema (§8.4) until the quantum lane lands. Primitive geometry only.

**Where things stand:** `echo/` does not exist. No sibling lane has any commits yet: platform, quantum, story-ui and art are all empty against main. So we build our modules against stated contracts and drive them from a dev harness that lives outside `echo/`.

**Boundaries:**
- We own `echo/game/` (except `audio.js`) and `echo/scene/` (except lighting/rain/props/buildings/effects).
- `echo/main.js` belongs to platform. We expose a single entry, `startGame({ root, quantum, ui })`, from `echo/game/app.js`, and platform's `main.js` will call it.
- Terminal and dialogue UI belong to story-ui. We emit `OPEN_TERMINAL {id}` and similar events. The graybox harness carries a throwaway dev terminal outside `echo/`.
- The fake quantum adapter is dev-only and lives outside `echo/`. It is labelled engine `documented_preview` and must never be presented as Qiskit output.
- Interactable positions are tied to the geometry, so gameplay owns them in `scene/district.js` (anchor ids). `data/` (story-ui) refers to them by id.

**The harness:**
- `dev/gameplay/harness.html` plus a fake adapter and a dev terminal.
- It is served from the repo root on each worker's own port.
- An importmap maps `three` to jsdelivr 0.186.1, which matches Qollab's by-name import.

**Workers (cap 2, both running in parallel now):**
1. `gameplay-quest-core`: `echo/game/eventBus.js`, `echo/game/state.js` (the full §9.1 machine, guards, idempotency, reset hooks), `echo/game/objectives.js` (only if story-ui has nothing), the fake adapter and the dev terminal under `dev/gameplay/`, and Node-run transition checks. Small and fast.
2. `gameplay-world-controller`:
   - Scene and renderer, plus the three-space graybox in district, alley, relay, rooftop and player.
   - Input, camera and controller with collision, and interactions.
   - `app.js` with `startGame`, plus the harness page.
   - Event-driven world reactions.
   - It codes against the eventBus/state API frozen below and merges worker 1's branch when that lands.

**Frozen API both workers obey:**
- `eventBus.js`: `createEventBus()` returns `{on(type, fn) → off, emit(type, payload)}`.
- `state.js`:
  - `QUEST_STATES` and `TRANSITIONS` follow §9.2, extended so BOOT→TITLE is `BOOTED`, TITLE START, and so on.
  - `createQuestMachine(bus)` returns `{state, send(event) → {ok, state, reason}, can(event), reset()}`.
  - On a successful transition it emits `quest:transition {from, to, event}` and `quest:enter:<STATE>`.
  - A repeated or invalid event returns `ok:false`, emits nothing and changes nothing.

**Next, after both land:** a full run in the harness from title to credits, recorded as screenshots and a video. Then a reviewer pass, then MERGE. Then hand the integration contract to platform and story-ui, and swap in the real quantum adapter once the quantum lane ships.

**Risks:**
- The 2 h worker budget against the size of worker 2's task. Mitigation: a checkpoint report within 1 h, and alley + relay first if it runs late.
- The `main.js` and data ownership seams. Mitigation: the frozen contract, reported in each report's requests section.
- A deadline miss. Mitigation: the one-room cut at Sat 17:00.
- Pointer lock in headless capture: verify behaviour through the synthetic-event path, and the owner checks real lock by looking.
=== END PLAN ===

=== AGENT name=gameplay-quest-core model=opus base=lane/gameplay/integration ===
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
=== END AGENT ===

=== AGENT name=gameplay-world-controller model=opus base=lane/gameplay/integration ===
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
=== END AGENT ===

=== LEARN ===
Consult 1: `echo/` didn't exist and no sibling lane had commits. So gameplay builds against frozen contracts:
- `startGame({root, quantum, ui})` from `echo/game/app.js`, which platform's `main.js` calls.
- The eventBus/questMachine API, stated in both briefs.
- Dev-only harness, fake adapter and dev terminal under `dev/gameplay/`, outside `echo/`, so nothing dev-only ships or counts toward the 100-file limit.

Interactable anchor positions live in `scene/district.js` because they are tied to the geometry. `data/` refers to them by id.
=== END LEARN ===

=== LEARN ===
The worker model key is assumed to be "opus" (the context did not name the keys). If a dispatch fails on the model key, check the loop's accepted keys before re-dispatching.
=== END LEARN ===
