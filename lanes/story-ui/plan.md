**Lane story-ui: plan as of consult 1 (Fri 2026-10-09 ~23:20 ET, T+4.5h)**

**Goal:** the story and interface from vision §4 and §6. That means a skippable opening, dialogue with subtitles (2 lines max), the HUD, and three terminals (copy booth, relay, teleport console) wired to the §8.4 quantum adapter with honest error states. It also means progressive hints, Declassified mode with the teach-back, pause and settings menus, keyboard navigation, visible focus, reduced motion and text scaling. This covers Plan rows 5 (G2, shared with gameplay) and 6 (G3, shared with art).

**State:** `echo/` does not exist yet. No other lane has landed anything. The platform lane owns `main.js`, `index.html`, the event bus and the shared contracts, and none of these exist yet. This lane must therefore build in a way that does not depend on them.

**Approach (decoupled vertical slices):**
- Every UI module in `echo/ui/` is a plain ES module with named exports. Each one creates its own DOM inside a root element passed in (`mount(root, deps)`), because `index.html` belongs to platform and `<script>` does not run on Qollab. Each one talks to the rest of the game through callbacks and injected dependencies, not globals. When platform's eventBus lands, the wiring is a few lines in `main.js` (platform's job).
- Names come verbatim from the vision: §9.1/§9.2 for quest states and events, §8.4 for `ExperimentResult`/`QuantumEngine`, §9.4 for interactable ids. Any naming the vision leaves open goes to platform as a contract request in the worker's report.
- Story data lives in `echo/data/*.js` as JS modules, not JSON, because JS cannot read project files on Qollab.
- All CSS goes in `echo/main.css`, because it is the only stylesheet Qollab loads. Each worker writes inside its own delimited section.
- The dev harness lives outside `echo/` at `evidence/story-ui/harness/`, so it never counts toward the 100-file limit. Each worker serves it on its own port.
- Terminals run against the §8.4 interface. Until the quantum lane ships its adapter, the harness passes in a stub labelled `documented_preview` that returns only textbook-exact values. The UI always shows the engine label and never presents preview data as a measurement.

**In flight (consult 1):**
1. `ui-shell`: `main.css` tokens (§6.2), `ui/hud.js`, `ui/dialogue.js`, `ui/menu.js` (title/pause/settings), `ui/accessibility.js`.
2. `story-data`: `data/story.js`, `data/objectives.js` (all §4 beats as subtitle-sized lines, hint ladders for §6.6, teach-back questions), plus a physics-claims check against §2.4/§7.
3. `terminals`: `ui/terminal.js` (the three terminals from §6.4/§6.5 and §4.2–4.4), with honest error, loading and fallback states and idempotent commit-once.

**Next (consult 2+):**
- Merge ui-shell first; terminals then rebases for `main.css`.
- Then `ui/declassified.js` and teach-back, `ui/credits.js` (blocked on owner credit names), and the opening sequence player (Shot A–D captions, skippable), which needs gameplay's camera hooks.
- Then an a11y pass: keyboard-only playthrough of every panel, 200% text, reduced motion, contrast audit with accesslint.
- Then integration with platform's `main.js` and gameplay's state machine, followed by a full graybox run in the local runner.

**Risks:**
- Contract drift with platform/gameplay. Mitigation: verbatim vision names, contract requests filed early.
- `main.css` merge conflicts. Mitigation: delimited sections and merge order.
- Physics wording errors in dialogue. Mitigation: story-data self-audits against §2.4/§7, and the red-team lane reviews later.
- G2 Sat 17:00: by Sat ~12:00 the UI must be integrated, or the lane falls back to one-room (§13).
- Credits blocked on owner names.