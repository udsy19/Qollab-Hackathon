=== PLAN ===
**Lane goal:** platform. G0 first: a Qollab-shaped `echo/` (body-fragment `index.html`, `main.js`, `main.css`). It renders a Three.js scene, calls a Qiskit Python module through `.callPromising` and `.toJs()`, and makes exactly one `backend.run`. Alongside it: a local Qollab-like runner in `tools/` and `echo/QOLLAB_SMOKE_TEST.md` for the owner. After G0, platform owns `main.js`, `index.html` and the shared contracts (event names, `ExperimentResult`, interactable ids). It also integrates every lane after each merge, runs full playthroughs, keeps `echo/` within Qollab's caps, and writes the README/project page, the 2:40 video script and the release. Plan rows 3, 7 and 8.

**Clock (ET):** now about Fri 23:20, and G0 is overdue. G1 is Sat 04:00, G2 Sat 17:00, G3 Sun 05:00, freeze Sun 14:00, submit Sun 19:00.

**Approach, in order:**
1. **G0 vertical slice (worker `g0-runner-smoke`):**
   - `echo/` minimal: a Three.js scene, a Python module under `echo/quantum/` called through `.callPromising` + `.toJs()`, and one guarded `backend.run` behind a button.
   - `tools/qollab-runner/`: a local runner that copies the documented Qollab JS-project contract as closely as it can, built from the live docs and the earlier org's research.
   - The smoke-test doc for the owner.
   - Evidence is screenshots from the local runner. Nothing gets called a "Qollab run" until the owner confirms one.
2. **Shared contracts in parallel (worker `shared-contracts`):**
   - The vision §8.4 `ExperimentResult` as a guarded JS validator, plus the Python-side shape documented for the quantum lane.
   - §9.1 quest states and the §9.2 transition table as frozen data, plus the event names (§9.3) and the interactable ids (§9.4).
   - One platform-owned file, so the other lanes can build against it tonight.
3. **After both merge:** brief every lane through owner-answers on the contract location. Then `main.js` becomes the integration point that boots the gameplay, scene, ui and quantum modules, starting with an empty-room playable shell.
4. **Later (rows 7, 8):** a caps-check script (≤100 files, ≤2 MB) written red-first; the README as the Qollab write-up (one paragraph per line, YouTube embed); the video script; three consecutive full runs.

**Done:** nothing yet (fresh lane).

**Risks:**
- **Running Qiskit in a local runner.** Stock Pyodide may not ship Qiskit (it has Rust extensions). Qollab must use its own build, maybe fetchable by GET from its CDN. The fallback is a dev-only CPython bridge, and it must be labelled honestly as "local runner (CPython)", not "Pyodide".
- **The JS→Python import mechanism** (`import * as m from 'quantum.mod'`) has to be copied exactly. A wrong copy hides a G0 failure until the owner runs it on Qollab.
- **The IonQ "Credits apply" label** is still unresolved.
- **The owner's Qollab run is the only real G0 proof**, and it needs their time tonight.
- **Contract location:** `echo/contracts.js` is my reversible choice; the question is sent to the owner.
=== END PLAN ===

=== AGENT name=g0-runner-smoke model=opus base=lane/platform/integration ===
**GOAL:** The owner uploads `echo/` to Qollab tonight, presses Run with the built-in simulator, and sees three things:
- a Three.js scene rendering;
- a panel showing a dict that a Qiskit Python module in the project computed (a real `Statevector` result, e.g. Bell-state probabilities), reached from JS via `.callPromising(...)` + `.toJs()`;
- after a "Verify on selected backend" button, counts from **exactly one** `backend.run`. A second press must refuse visibly, not call again.

Before that run, every agent on this project can develop and screenshot against a local runner that behaves like Qollab closely enough that "works locally" predicts "works on Qollab".

**VISION:** ECHO: ONE OF ONE (`ECHO_MASTER_VISION.md`) is a Qollab-native Three.js game with real Qiskit puzzles. This is gate G0 (vision §15/§16, `ROADMAP_48_HOURS.md`), the platform proof everything else stands on. It is overdue (was due Fri 22:00 ET).

**WHAT WE ARE BUILDING:**
1. `echo/index.html`: a body fragment only. No html/head/body tags, no `<script>`.
2. `echo/main.js`: the entry. It imports `three` by bare name.
3. `echo/main.css`.
4. A tiny Python module under `echo/quantum/`, e.g. `echo/quantum/smoke.py`. The quantum lane owns that folder later; you may add only this one smoke module, and say so in your report.
5. `echo/requirements.txt` if the docs call for one.
6. `tools/qollab-runner/`: the local runner, outside `echo/`. It may use Node for serving only.
7. `echo/QOLLAB_SMOKE_TEST.md`: exact owner steps. Which upload shape to use, which backend to pick, what to click, what they should see (with your local-runner screenshot as the reference), and what each failure would mean. Include a separate optional IonQ-simulator step, and say clearly that it may show "Credits apply".

**WHAT HAS NOT WORKED / KNOWN TRAPS:** Nothing has been tried on ECHO. The earlier org measured these:
- `<script>` in `index.html` does not run.
- JS cannot read project files.
- A plain (non-`callPromising`) Python call on an IonQ backend fails with an XHR `ConnectionError`.
- Pyodide on Qollab is Python 3.14 with Qiskit 2.x, and `three` 0.186.1 imports by name.
- Stock Pyodide may NOT have Qiskit. Find out how Qollab gets it: read the live docs, and if needed its shipped JS bundle (GET only, read-only).
- If a faithful in-browser Qiskit is impossible locally, a dev-only bridge to the venv's CPython Qiskit is acceptable. It must label itself on screen as "local runner: CPython Qiskit", and the report must say what this does NOT prove (Pyodide compatibility).
- Do not invent the runtime. Every behaviour the runner mimics must cite a doc line or an observed fact.

**Read first (vault):**
- `vault/AGENTS.md`
- `vault/Index.md`
- `vault/Research/qollab-platform-and-submission.md` (essential)
- `QOLLAB_DEPLOYMENT.md`
- vision §8.2, §8.4–8.6 and §10.7
- `.claude/rules/qollab-runtime.md`
- `/Users/udsy/agent-org-qollab-hackathon/lanes/unlocked/reports/0001-ionq-sim-spike.md` (read-only)

Then fetch https://qollab.xyz/learn/docs/js-qiskit-projects, /runtime-environment and /run-your-code. It is a Nuxt SPA, so render it with headless Chrome or defuddle. Base the bridge and import shape (`import * as m from '<dotted.path>'`, how `backend` is exposed in JS, how `QuantumCircuit` is built from JS or Python) on what these say. Save what you learn to `vault/Research/` (with sources), linked from the hub.

**Start:** `node scripts/where.mjs runner --branches` and `git grep -i pyodide`, to reuse anything that exists.

**Deliver** (commits on your branch):
- the files above;
- a runner README (one command to start it, on its own port);
- screenshots under `renders/` or `evidence/platform/g0/` (with a README) showing: the scene, the bridge dict, the one-job counts, and the refusal on a second press.

**Prove the one-job guard** in two ways:
1. a runner-side counter that raises on a second `backend.run`, the way IonQ does;
2. a sabotage run where you remove the JS guard and show the runner going red.

Prove provenance: change a visible build token, reload, and read it back from the served page (law 16).

**How I will judge:**
- The screenshots, read against the doc citations.
- Whether the smoke test lets the owner run it without asking anything.
- An `echo/` file listing within the caps.
- No claim of a Qollab or IonQ run anywhere.

**Report** goes in `/Users/udsy/agent-org/lanes/platform/reports/`:
- Open with a "Vault check".
- Then: TL;DR, what the runner mimics (with citations), what it does NOT mimic, commands with exit codes, evidence paths, the nulls from your sabotage round, and `## Questions for the owner`.
- Checkpoint report within 1 h, even if partial.
=== END AGENT ===

=== AGENT name=shared-contracts model=opus base=lane/platform/integration ===
**GOAL:** Every lane (gameplay, story-ui, quantum, art) can build tonight against one frozen, platform-owned definition of how the game talks to itself. They should not each invent state names, event names, terminal ids or result shapes that then fail to join at integration. A wrong name must fail loudly at the call site, not silently do nothing.

**VISION:** ECHO's quest is a deterministic state machine (vision §9) driven by named events (§9.3). Its physics results cross the JS↔Python bridge as typed results (§8.4), so that the UI never confuses simulator counts with exact probabilities and never shows invented numbers (CLAUDE.md "typed result schemas").

**WHAT WE ARE BUILDING:** A single platform-owned module, `echo/contracts.js`: plain ES module, named exports, no Node, no bundler. This location is provisional and is with the owner as a question, so keep it to one file that can move with one import change. It contains:
1. `QUEST_STATES` (vision §9.1, verbatim) and `TRANSITIONS` (the §9.2 table), frozen, plus a pure `transition(state, event)` that returns `{ok, state, reason}`.
2. `EVENTS`: world/quest event names for the §9.3 consequences and the bus. Derive these from the vision; do not make them up beyond it, and list any you had to add with a reason.
3. `INTERACTABLE_IDS`: from §9.4 plus the rooftop terminal and clone booth as the vision names them.
4. `ENGINE_KINDS` and `validateExperimentResult(obj)`. The validator is a guarded check of the §8.4 shape. It rejects: unknown engine; probabilities that don't sum to 1±1e-9; `counts` present under engine `exact_qiskit_local`; `measurementBits` outside {0,1}; missing `facts`. It returns a list of errors, never throws silently.
5. A short `echo/CONTRACTS.md` for the other lanes. It covers the exact Python dict shape the quantum lane's functions must return (plain serialisable values only; m0 = source readout, m1 = Alice's Bell half; X iff m1=1, Z iff m0=1), and how to propose a change (through platform only).

**WHAT HAS NOT WORKED:** Nothing tried on ECHO yet. The project-wide failure modes are optimising against tests instead of the product, and building behind flags nobody switches on.

**Read first:**
- `vault/AGENTS.md` and `vault/Index.md`
- vision §8.2, §8.4, §8.7 and §9 (all of it)
- §10.x wherever it shows adapter or state code
- `CLAUDE.md` (code conventions)
- `.claude/rules/lane-ownership.md`, `.claude/rules/no-bloat.md`

Run `node scripts/where.mjs ExperimentResult --branches` and `git grep -n "QUEST_STATES\|transition("` first.

**Checks you derive and write FIRST, watched red:** a small Node test under `tools/contract-check/` (Node is fine outside `echo/`).
- It replays the full happy path TITLE→CREDITS through `transition`.
- It proves every state in §9.1 is reachable. Derive the expected set from the vision text, not from your own table (law 8).
- It proves invalid events are refused.
- It runs the validator against good and bad fixtures.

**Sabotage round:** delete a transition, misspell a state, flip the probability tolerance. Report which ones went red and which (the nulls) did not.

**Also prove it loads in a browser:** a throwaway page in `tools/` that imports `echo/contracts.js` as an ES module and prints the happy-path trace, plus a screenshot.

**How I will judge:**
- The red-then-green log.
- The sabotage nulls.
- The browser screenshot.
- Whether `CONTRACTS.md` is enough for the quantum lane to write `formats.py` without asking.

**Report** goes in `/Users/udsy/agent-org/lanes/platform/reports/`:
- Open with a "Vault check".
- Then: TL;DR, decisions you made that the vision did not settle (each one becomes an owner question), commands with exit codes, evidence paths, and `## Questions for the owner`.
- Checkpoint within 1 h.
=== END AGENT ===

=== ASK_OWNER ===
1. **G0 needs you on Qollab tonight.** Once `echo/QOLLAB_SMOKE_TEST.md` lands (target: within ~1.5 h), can you upload `echo/` and run it once on the **built-in simulator**? Please paste what you see, or a screenshot, into `owner-answers.md`. Nothing else can prove G0, and I will not report it done without your confirmation.
2. **IonQ simulator label.** Signed out, Qollab labelled the IonQ remote simulators "Credits apply", while the docs say they are free. When signed in, what does Select QPU show for IonQ Aria/Forte simulators, and may we spend credits on **one** job per test run if it says credits?
3. **Where the shared contracts live.** I plan one platform-owned file, `echo/contracts.js` (quest states, transitions, event names, interactable ids, the `ExperimentResult` validator), plus `echo/CONTRACTS.md` for the other lanes. The vision's §8.2 tree has no slot for it. OK, or do you want it elsewhere?
4. **Credits.** Which names go in the in-game credits and the README? (Your ruling says to ask before writing them; this is needed by Sun 05:00, not tonight.)
=== END ASK ===

=== LEARN ===
Lane opened 2026-10-09 ~23:20 ET with G0 overdue.

G0 cannot be marked done on local evidence. Only an owner-confirmed Qollab run recorded in `owner-answers.md` closes row 3; local-runner screenshots are necessary but not sufficient.

The biggest local-runner risk is Qiskit-in-Pyodide. A CPython bridge is allowed only if it is labelled on screen and its report states that it does not prove Pyodide compatibility.
=== END LEARN ===
