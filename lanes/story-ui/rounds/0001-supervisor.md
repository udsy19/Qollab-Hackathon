=== PLAN ===
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
=== END PLAN ===

=== AGENT name=ui-shell model=opus base=lane/story-ui/integration ===
**GOAL:** A first-time player sees a readable, cinematic interface around the game: title screen, HUD, 2-line subtitled dialogue, and pause/settings menus. They can drive all of it from the keyboard alone, with visible focus, and it honours reduced-motion and text scaling up to 200%.

**VISION:** ECHO: ONE OF ONE (`ECHO_MASTER_VISION.md` §6.1–6.3, §6.6, §4.1 Shot D, §3.1 tooltips, §12.5). Judges play on Qollab in a desktop browser. The blind-tester bar is title → three missions → ending without help.

**WHAT WE ARE BUILDING:** The Qollab-native project in `echo/`. You own only these story-ui files:
- `echo/main.css`: tokens and base, HUD, dialogue and menus. Put each in its own section headed `/* ==== <module> ==== */`. Leave room for a later `/* ==== terminal ==== */` section written by another worker.
- `echo/ui/hud.js`, `echo/ui/dialogue.js`, `echo/ui/menu.js`, `echo/ui/accessibility.js`.

Each module exports named functions. Each builds its own DOM inside a root element passed in, e.g. `mountHud(root)`, which returns `{setObjective, setCountdown, setCapsuleState, showPrompt, hidePrompt, showTooltip}`. The dialogue module plays beats `{speaker, text}`, enforces 2 lines maximum, and can skip to the full caption immediately. The menu module provides title (Start / Settings / Controls), pause (ESC: Resume / Settings / Restart), and settings: subtitles, reduced motion, text scale 100–200%, quality low/med/high, volume. Settings live in memory only (no localStorage etc. on Qollab). Changes go out through an `onChange` callback and a `data-` attribute or class on the root, so CSS and other lanes can react.

You do NOT own `index.html`, `main.js` or the event bus. Those belong to the platform lane and do not exist yet. Do not create them. If you need a contract (event names, settings shape), put it in your report as a request to platform.

**Hard constraints:**
- No bundler or npm in `echo/`, and `<script>` in HTML does not run.
- Fonts: system stack, or an OFL font loaded by full https URL with its license recorded.
- Panels use `rgba(6,13,24,0.92)` with a 1px cool outline.
- Status states must not be shown by colour alone.
- UI transitions run 150–300ms, and reduced motion disables them.

**WHAT HAS NOT WORKED (org-wide):** optimising against tests instead of the product; building behind flags nobody turns on; judging the wrong artifact; meta-work instead of product work. Nothing has been tried on this lane yet.

**Vault notes to read first:**
- `vault/AGENTS.md`
- `vault/Home.md`
- `vault/Index.md`
- `vault/Research/qollab-platform-and-submission.md`: the measured runtime facts (main.css is the only stylesheet; JS can't read project files)
- `vault/Design/lanes-and-supervisors.md`

**Where to start:**
- Build a harness at `evidence/story-ui/harness/shell.html`. It sits outside `echo/` on purpose. It imports your modules by relative path, links `../../../echo/main.css`, and puts a dark placeholder backdrop where the canvas will go.
- Serve the repo with `python3 -m http.server` on a port of your own (pick 87xx, not 8000).
- Drive it headlessly (puppeteer MCP or a browser-tester sub-agent).

**Deliver:** committed modules and harness on your branch, plus screenshots in `evidence/story-ui/ui-shell/` with a README covering:
1. title screen with the focus ring visible
2. HUD in the §6.3 layout ("ECHO // DISTRICT 09 … GRID SHUTDOWN 08:42 / OBJECTIVE 02 … / Q-SOURCE: PRESERVED … [E] INTERACT")
3. dialogue showing a 2-line beat, plus proof that a long line is split rather than overflowing
4. pause and settings reached by keyboard only (list the key sequence)
5. the same HUD and dialogue at 200% text scale
6. reduced motion on, with a computed-style check showing transitions at 0

Also run accesslint (`audit_live`) on the harness and report the violations, fixed and remaining.

**How I will judge:** by looking at the screenshots. Every interactive element must be reachable by Tab/Enter/ESC with focus always visible. Nothing may overflow at 200%. The screenshots must be from the build you committed: put a version token in the harness and show it in the screenshot. Exit codes and paths must be included.

**Report:** `/Users/udsy/agent-org/lanes/story-ui/reports/ui-shell.md`. Open with a **Vault check** (notes read, what was known, what you reused, what is stale). Then TL;DR, evidence (command + exit code + path), nulls, `## Contract requests for platform`, and `## Questions for the owner`. Write a checkpoint report within 1 h even if the work is partial (mark it PARTIAL). Write durable findings to the vault and run `node scripts/vault-hubs.mjs`.
=== END AGENT ===

=== AGENT name=story-data model=opus base=lane/story-ui/integration ===
**GOAL:** Every word the player reads in ECHO exists as clean, subtitle-ready data that is true to the physics:
- opening, three missions, ending
- Mica's radio, VEGA, MIRROR, Rin
- objectives and HUD strings
- the progressive hint ladder for every puzzle
- the "every failure says why" lines
- the Declassified teach-back questions and answers

**VISION:** `ECHO_MASTER_VISION.md` §4.1–4.5 (story beats, verbatim where given), §2.2 (characters), §2.4 (what NOT to claim), §6.6 (hints: Hint 1 prompts inspection, Hint 2 names the resource, Hint 3 states the operation; no penalty), §7 (normative physics), and §9.1/§9.2 (quest states and events; key your data to these names verbatim). The bar: a blind tester finishes without help and can answer the three teach-back questions.

**WHAT WE ARE BUILDING:** The Qollab project in `echo/`. You own:
- `echo/data/story.js`: dialogue beats grouped by sequence id. Each beat is `{speaker, text}`, with text fitting 2 subtitle lines at about 42 chars per line. Split longer beats into consecutive beats rather than truncating them. Where the vision gives a line, use it verbatim.
- `echo/data/objectives.js`: an objective string per quest state, plus hint ladders per puzzle.
- Teach-back content, either in `story.js` or in a `data/teachback.js` file. Keep the file count low: `echo/` has a hard cap of 100 files.

Plain ES modules with named exports and data only, because JS cannot read JSON project files on Qollab. You do NOT own `ui/`, `game/`, `quantum/`. If gameplay or platform need a different key shape, file it as a contract request.

Physics rules:
- Never claim FTL messaging, cloning an unknown state, "certified quantum randomness" or teleporting matter.
- Entanglement was pre-shared before the crisis.
- m0 = source readout, m1 = local Bell half; X iff m1=1, Z iff m0=1.
- The story token is consumed once at commit. Calibration uses fresh prepared states.
- Credits: do NOT write team names. The owner has not given them, so leave a clearly marked placeholder. Include "This effort is supported by Qollab & IonQ".

**WHAT HAS NOT WORKED (org-wide):** optimising against tests instead of the product; meta-work instead of product work. Nothing has been tried on this lane yet.

**Vault notes:** `vault/AGENTS.md`, `vault/Home.md`, `vault/Index.md`, `vault/Research/qollab-platform-and-submission.md`.

**Where to start:** read §4, §2.4 and §7 fully, then write the data.

Then write a small Node check at `evidence/story-ui/story-data/check.mjs`. It is local tooling only and lives outside `echo/`. Write it FIRST and watch it fail on a deliberately bad fixture. It must verify:
- every beat fits 2×42 characters
- every speaker is in the cast
- every §9.1 state that the player sees has an objective
- every puzzle has exactly 3 hints
- forbidden-claim phrases are absent

Derive the forbidden phrases from §2.4's meaning, not just its words. Then run a sabotage round (inject an overlong line, a missing hint, a "faster than light" line) and report what did NOT go red.

**Deliver:** the data files; the check with its exit codes; `evidence/story-ui/story-data/script.md`, a human-readable rendering of the full script in play order (this is what the owner will read); and a list of every place where you wrote new text beyond the vision's verbatim lines, so the owner can review it.

**How I will judge:** I will read `script.md` start to finish. It must read as a coherent ~10-minute story, with every physics statement matching §7 and every hint ladder escalating properly.

**Report:** `/Users/udsy/agent-org/lanes/story-ui/reports/story-data.md`. Open with a Vault check, then TL;DR, evidence (command + exit code + path), nulls, `## Contract requests for platform/gameplay`, and `## Questions for the owner`. Write a checkpoint within 1 h (PARTIAL if needed).
=== END AGENT ===

=== AGENT name=terminals model=opus base=lane/story-ui/integration ===
**GOAL:** A player can operate the three in-world terminals by mouse or keyboard alone:
- **PALISADE copy booth** (§4.2, §6.4): |0>, |1>, |+> → DUPLICATE. Basis states "match"; |+> gives a Bell pair, TWO INDEPENDENT COPIES: NO. Then "Show me why" and the deduction choice (increase voltage vs reroute; both allowed, no punishment).
- **Relay** (§4.3): prepare the Bell pair, choose a sender local op I/X/Z, SEND. The receiver's local marginal stays uniform for all three. The player can compare the receiver-only view with the paired view.
- **Teleport console** (§4.4, §6.5): repair the link, run the Bell measurement on a fresh test state, show m0/m1, set the X and Z corrections (all four choices possible), VERIFY DRY RUN with fidelity, then COMMIT STORY TRANSFER exactly once.

Every failure tells the player why. Hints come on request in three escalating levels. ESC always backs out without softlocking. Every result shows which engine produced it.

**VISION:** `ECHO_MASTER_VISION.md` §4.2–4.4, §6.1 layer 2 (movement disabled and mouse free while open; ESC closes), §6.4–6.6, §7 (normative physics), §8.4 (the adapter contract `QuantumEngine` / `ExperimentResult` / `EngineKind`; use these names verbatim), §8.6 and §12.3 (honest loading and failure states: "CALIBRATING"; "Quantum backend verification unavailable; educational circuit validated locally"; never "IonQ verified" unless true), §9.2 events and §9.3 (idempotence: opening a terminal twice never replays an irreversible transfer).

**WHAT WE ARE BUILDING:** `echo/ui/terminal.js`, which you own, plus a `/* ==== terminal ==== */` section at the END of `echo/main.css`. Another worker (ui-shell) is writing the tokens and base sections of that file right now. Use plain CSS custom-property fallbacks so you don't depend on their names. Before your final commit, `git fetch` and rebase onto `lane/story-ui/integration` if it has moved, and resolve `main.css` by keeping both sections.

API shape:
- `mountTerminal(root, {engine, onEvent, getHint})`
- `open(terminalId)` with ids `copy_booth`, `relay_core`, `classical_socket` (§9.4 verbatim)
- `close()`

The terminal emits the §9.2 event names through `onEvent` and never owns quest state. You do NOT own `quantum/`, `game/`, `main.js`, `index.html`, or the event bus. File any contract you need as a request to platform.

**Physics truth is non-negotiable:**
- m0 = source readout, m1 = local Bell half.
- The correct correction is X iff m1=1 and Z iff m0=1. Show the bit order explicitly.
- A wrong correction gives a real fidelity below 1 and explains why. Do not hard-fail with no reason.
- COMMIT is disabled until a dry run passes. After commit, the source shows as consumed and COMMIT can never fire again (idempotent).

**Engine:** The real engine is the quantum lane's job and does not exist yet. In your harness, pass a stub that implements §8.4 with `engine: 'documented_preview'`. It may return only textbook-exact values (e.g. purity 0.5 for each half after CNOT on |+>; fidelities from the closed-form branch table §10.6). Your UI must display the engine label on every result, so preview data is never presented as a measurement. The stub lives in the harness, NOT in `echo/`.

Handle these engine states: pending (CALIBRATING, still interactive, no frozen UI), rejected promise or error (honest message plus retry), and malformed result (a guarded schema check that refuses and says so).

**WHAT HAS NOT WORKED (org-wide):** optimising against tests instead of the product; building behind flags nobody switches on; judging the wrong artifact. Nothing has been tried on this lane yet.

**Vault notes:** `vault/AGENTS.md`, `vault/Home.md`, `vault/Index.md`, `vault/Research/qollab-platform-and-submission.md`.

**Where to start:**
- Harness at `evidence/story-ui/harness/terminals.html`, outside `echo/`.
- Serve with `python3 -m http.server` on your own 88xx port.
- Drive it headlessly (puppeteer MCP or a browser-tester sub-agent).

**Deliver:** screenshots in `evidence/story-ui/terminals/` with a README. Required shots:
- each terminal at each step
- |+> failing with its reason
- relay marginals for I/X/Z
- all four m0/m1 cases, with right and wrong corrections and the resulting fidelity
- commit, then a second attempt refused
- engine error state
- CALIBRATING state
- ESC mid-flow, then reopen with state intact

Also provide: a keyboard-only key sequence for one full teleport run, and an accesslint `audit_live` result. Write the event-log check FIRST and watch it fail. It must assert that the emitted §9.2 events appear in order and that COMMIT_TRANSFER is emitted at most once under double-clicks.

**How I will judge:** screenshots from the committed build, with a version token visible. The physics shown must match §7 and the engine label must always be visible.

**Report:** `/Users/udsy/agent-org/lanes/story-ui/reports/terminals.md`. Open with a Vault check, then TL;DR, evidence (command + exit code + path), nulls, `## Contract requests for platform/quantum`, and `## Questions for the owner`. Write a checkpoint within 1 h (PARTIAL if needed).
=== END AGENT ===

=== ASK_OWNER ===
1. **Credit names:** whose names should appear in the in-game credits and the README team credits, and in what form (real names, handles, roles)? Workers will leave a marked placeholder until you answer. The required line "This effort is supported by Qollab & IonQ" is already planned.
2. **New dialogue text:** the vision gives verbatim lines for most beats. Where it doesn't (hint ladders, failure explanations, teach-back answers, the ending), may the story-data worker write new lines in the same voice for your review in `evidence/story-ui/story-data/script.md`? Or do you want to approve every new line before it ships? Work continues either way; this only decides whether new text can merge before you have read it.
=== END ASK ===

=== LEARN ===
Story-ui modules must not depend on anything the platform lane owns. On Qollab, `<script>` in `index.html` does not run, `main.css` is the only stylesheet loaded, and JS cannot read project files (`vault/Research/qollab-platform-and-submission.md`). So:
- UI modules build their own DOM inside a root element passed in.
- Story data ships as JS modules, never JSON.
- All CSS lives in delimited sections of `echo/main.css`.
- Dev harnesses live outside `echo/` (`evidence/story-ui/harness/`) to stay under the 100-file cap.

`main.css` is a merge hot spot: merge ui-shell first, then the other workers rebase.
=== END LEARN ===

=== LEARN ===
Until the quantum lane ships its §8.4 adapter, terminal work uses a harness stub with `engine: 'documented_preview'` that returns only textbook-exact values. The UI must always display the engine label. A screenshot without the label, or with stub values presented as Qiskit or backend output, is grounds to refuse the merge.
=== END LEARN ===
