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