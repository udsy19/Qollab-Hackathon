
- 2026-10-10 consult 1: Consult 1: `echo/` didn't exist and no sibling lane had commits. So gameplay builds against frozen contracts:
- `startGame({root, quantum, ui})` from `echo/game/app.js`, which platform's `main.js` calls.
- The eventBus/questMachine API, stated in both briefs.
- Dev-only harness, fake adapter and dev terminal under `dev/gameplay/`, outside `echo/`, so nothing dev-only ships or counts toward the 100-file limit.

Interactable anchor positions live in `scene/district.js` because they are tied to the geometry. `data/` refers to them by id.

- 2026-10-10 consult 1: The worker model key is assumed to be "opus" (the context did not name the keys). If a dispatch fails on the model key, check the loop's accepted keys before re-dispatching.
