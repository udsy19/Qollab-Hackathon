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