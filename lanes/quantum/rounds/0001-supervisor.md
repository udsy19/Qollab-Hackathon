=== PLAN ===
**Lane goal (G1, due Sat 2026-10-10 04:00 ET; plan row 4).** Build `echo/quantum/{__init__,cloning,entanglement,teleportation,formats,qollab_job}.py` to match vision §7 and §10.3–10.7. Every function returns JSON-safe dicts for the JS bridge (`callPromising(...).toJs()`). Tests go in `echo/tests/` and cover:
- basis states copy; |+>, |−> and phase states do not (reduced purity 0.5, and the output is not ψ⊗ψ);
- receiver marginal stays 50/50 for sender I/X/Z (partial_trace gives I/2), and I vs X shows a joint-correlation difference;
- teleportation for 6+ states × all 4 branches at fidelity ≥ 0.999999, plus the "no corrections" average that is independent of the source;
- an endianness fixture;
- the deferred-measurement circuit labelled as a verification, not a link;
- the one selected-backend Bell verification.

**Approach: two workers in parallel (cap 2), with no file overlap.**
1. `quantum-core` owns `cloning.py`, `entanglement.py`, `teleportation.py`, `formats.py`, `__init__.py`, `tests/test_{cloning,entanglement,teleportation}.py`, and the proposed `ExperimentResult` contract note in the vault.
2. `backend-job` owns `qollab_job.py`, `tests/test_qollab_job.py` (endianness fixture and counts parsing), and a research note on how a JS/Qiskit project reaches `backend`: from JS (§10.7) or from a Python module. It also checks whether our Qiskit calls run under Pyodide (Py 3.14, qiskit ≥2.5.2). It uses the §8.4 field names verbatim so `formats.py` can absorb them when I merge.

**Contract with the platform lane.** Platform owns the shared `ExperimentResult` schema. We propose it as `vault/Design/experiment-result-contract.md` (status: proposed), taking vision §8.4 verbatim and adding fields only with a stated reason. Platform rules on it. Likely split: `backend.run` lives in `main.js`, which platform owns. Quantum supplies the circuit spec and the counts→result interpretation.

**Done:** nothing yet. Fresh start; no `echo/` directory exists.

**Next:** judge both reports. Merge core first, then backend-job, reconciling it onto `formats.py`. Then send a red-team or reviewer pass covering:
- gate independence: expected values come from hand-derived amplitudes, not from the code under test;
- a sabotage round: swap the m0/m1 correction mapping, drop the H, flip endianness. Each must turn the tests red.

Then a Pyodide smoke test through the local runner, coordinated with the platform lane.

**Risks:**
- Pyodide's Qiskit API may differ from local qiskit 2.5.
- Ambiguity over whether `backend` is reachable from Python in JS projects.
- Bitstring endianness.
- Schema drift with platform.
- Over-claiming: never say "ran on IonQ/Qollab" without the owner's confirmation.
=== END PLAN ===

=== AGENT name=quantum-core model=opus base=lane/quantum/integration ===
**GOAL.** The game's three quantum puzzles are driven by real local Qiskit math. When a player at the replication booth tries to copy |+>, the terminal shows a truthful result computed by Qiskit: the copies are entangled and each has purity 0.5. At the relay, Bob's side stays at 50/50 whatever Alice does. At the rooftop, every combination of Bell-measurement bits and X/Z corrections gives a fidelity that Qiskit actually computed. You are building the Python engine and its tests. The game UI is not yours.

**VISION.** ECHO: ONE OF ONE teaches no-cloning, no-signalling and teleportation through gameplay. Judges (Qollab × IonQ) score technical execution, and the owner's line is "truthful physics". Read vision §7 (normative), §8.2 (tree), §8.4 (adapter contract), §10.2–10.6, and CLAUDE.md "Code and quality conventions".

**WHAT WE ARE BUILDING.** A Qollab JS/Qiskit project rooted at `echo/`. Python modules live in `echo/quantum/` and are imported from JS as `quantum.cloning`, etc. Each one is called with `fn.callPromising(args)` and the result converted with `.toJs()`. That means plain dicts, lists, str, float, int and bool only. No numpy scalars, no complex numbers, no Qiskit objects. Runtime: Pyodide, Python 3.14, Qiskit ≥2.5.2, NumPy 2. Use only `qiskit` core and `qiskit.quantum_info` (`Statevector`, `DensityMatrix`, `partial_trace`, `state_fidelity`, `Operator`). No Aer, no matplotlib draw. `qc.draw(output="text")` is fine. You own exactly these files: `echo/quantum/__init__.py`, `cloning.py`, `entanglement.py`, `teleportation.py`, `formats.py`, `echo/tests/test_cloning.py`, `test_entanglement.py`, `test_teleportation.py`, `echo/tests/smoke_plan.md`. Another worker owns `qollab_job.py` and `test_qollab_job.py` in parallel. Do not create those.

What each module must provide (the API names are your choice, but they must cover the §8.4 `QuantumEngine` methods):
- **cloning**: naive-CNOT clone for states zero, one, plus, minus, phase ((|0>+i|1>)/√2) and at least one generic Bloch point. Return the reduced purities of both outputs, the fidelity of each output with the input, and whether the joint state equals ψ⊗ψ.
- **entanglement**: Bell pair with sender I/X/Z. Return the receiver marginal from `partial_trace` and the full joint Z-basis probabilities. The joint probabilities show the I vs X correlation difference, visible only once both logs are compared.
- **teleportation**, both parts of §10.5:
  - (a) A **branch model**. For a given input state and given live bits (m0 = source readout, m1 = Alice's Bell half), project the Bell measurement and report that branch's probability (0.25 each in the ideal case). Apply the player's chosen X/Z to Bob's conditional state, then return the Qiskit-computed fidelity. Correct choice gives 1. Wrong choices give the true lower values: compute them, never hardcode them. Correction rule: **X iff m1=1, Z iff m0=1.** Registers: q0=source, q1=Alice's Bell half, q2=Bob. Gates: `H(q1);CX(q1,q2);CX(q0,q1);H(q0)`.
  - (b) A **deferred-measurement verification** with `CX(q1,q2);CZ(q0,q2)`. Its result must carry explicit labelling as a mathematical verification, not a physical link, for example a `facts` entry plus an `engine`/`kind` field.
  - Also provide a sampled single "live commit" branch draw for the story token. Use an injectable RNG/seed so tests are deterministic. It is presented as one sample, not proof.
  - Also provide the "corrections withheld" check: Bob's state averaged over branches is I/2 for every input.
- **formats**: the guarded builder for the §8.4 `ExperimentResult`. Use vision field names verbatim. `engine` is one of `exact_qiskit_local | qollab_selected_backend | documented_preview`. Round floats and convert everything to plain Python types. Raise on any field that is not JSON-safe. Never mix exact probabilities with shot counts: `probabilities` is for exact results, `counts` is for sampled results. Show that `json.dumps` of every result succeeds.
- Write the proposed contract as `vault/Design/experiment-result-contract.md` (frontmatter `status: proposed`). Include the schema, every added field with its reason, and one example per experiment. The platform lane owns the final schema; you are proposing.

**WHAT HAS NOT WORKED.** Nothing yet on ECHO (fresh start). Org-wide failures to avoid:
- optimising against a test suite instead of the goal;
- tests whose expected values come from the code under test;
- claiming results you didn't produce.

Known traps:
- Qiskit is little-endian: qubit 0 is the rightmost bit of a label, and `partial_trace(state, [k])` traces OUT qubit k.
- The §10.3 reference sets `isIndependentCloning` by state name. Derive it from the computed state instead.
- The §10.5 reference is only the deferred check. The branch model is mandatory.

**VAULT NOTES TO READ FIRST.**
- `vault/AGENTS.md`, `vault/Home.md`, `vault/Index.md`
- `vault/Missions/echo-hackathon-submission.md`
- `vault/Research/qollab-platform-and-submission.md`
- `.claude/rules/gate-independence.md`, and the cases at `vault/Design/gate-independence-cases.md`

**WHERE TO START.** Run `node scripts/where.mjs cloning --branches` to confirm nothing exists. Write the tests first, from hand-derived physics in the test file itself: explicit amplitude vectors, 1/√2, I/2 matrices. Watch them fail, then implement. Test with the venv: `/Users/udsy/PycharmProjects/Qollab-Hackathon-Quantum-Unlocked/.venv/bin/python -m pytest echo/tests`.

**HOW I WILL JUDGE IT.**
1. Expected values are independent of the implementation.
2. Teleportation covers ≥6 states × 4 branches × all 4 correction choices, with fidelity ≥ 0.999999 exactly when the choice follows the rule.
3. A **sabotage round** is reported with exit codes. Each of these must turn red: swap the X/Z↔m0/m1 mapping; remove the H in the Bell measurement; trace out the wrong qubit; return a hardcoded fidelity of 1.0. Report anything that stayed green.
4. Every return passes `json.dumps`.
5. No forbidden claims in strings ("certified random", "instant message", and similar).
6. A short printed transcript of each experiment's result dict, saved under `evidence/quantum-core/` with a README. Here the Python output is the visible evidence.

**REPORT.** Write `lanes/quantum/reports/quantum-core.md` with a checkpoint within 1 h. It opens with a **Vault check**, then: what was built, commands with exit codes, artifact paths, the sabotage table including nulls, and `## Questions for the owner` if any. Write measured findings to `vault/Reports/` and run `node scripts/vault-hubs.mjs`. Commit to your branch.
=== END AGENT ===

=== AGENT name=backend-job model=opus base=lane/quantum/integration ===
**GOAL.** At the end of ECHO, the judge sees exactly one honest job on the backend they selected in Qollab: a Bell-pair correlation circuit whose counts the game shows truthfully. It is labelled as a selected-backend Bell verification, never as "teleportation on IonQ". The game must never fire a second `backend.run` in a run, because IonQ allows one job per run and a second one stops the run. You are building `echo/quantum/qollab_job.py`, its tests, and the research that settles how the job is actually reached.

**VISION.** Vision §10.7, §7.5 and §8.4 (`verifySelectedBackendOnce`, `engine: 'qollab_selected_backend'`). Also `QOLLAB_DEPLOYMENT.md` and `.claude/rules/qollab-runtime.md`. The `backend` is injected: never hardcode one, never require a key, at most one `backend.run`.

**WHAT WE ARE BUILDING.** A Qollab JS/Qiskit project rooted at `echo/`. JS imports Python modules by dotted name and calls them with `callPromising`. You own only `echo/quantum/qollab_job.py`, `echo/tests/test_qollab_job.py`, and a research note. A parallel worker owns `formats.py` and the other quantum modules. Build your result dict with the exact §8.4 `ExperimentResult` field names: `experiment`, `engine`, `circuitDescription`, `qubits`, `parameters`, `counts`, `facts`. I will reconcile it onto `formats.py` at merge. Do not create `formats.py`.

**Questions to settle with sources** (Qollab docs are the source of truth: runtime-environment, js-qiskit-projects, run-your-code, compute-backends):
1. In a **JS/Qiskit** project, where does `backend` live: a JS global (§10.7 calls `backend.run` from JS), a Python global usable from an imported module, or both? Does a Python call need `callPromising` to reach a remote backend? The research note says a plain call fails with an XHR ConnectionError.
2. What does `get_counts()` return through `.toJs()`, and in which bit order for a measured register?
3. Does Pyodide's Qiskit (Py 3.14, qiskit ≥2.5.2) support every API that we and the parallel worker use: `QuantumCircuit`, `Statevector`, `DensityMatrix`, `partial_trace`, `state_fidelity`, and `draw(output='text')`?

Read the earlier org's evidence, read-only:
- `/Users/udsy/agent-org-qollab-hackathon/lanes/*/reports/`
- branch `lane/unlocked/ionq-sim-spike` in `/Users/udsy/PycharmProjects/Qollab-Hackathon`, using `git -C … show` and never checking it out over someone's work.

Deliverables:
- **(a)** `qollab_job.py`:
  - a pure function that builds the Bell verification circuit, plus a JSON-safe description of it, so whichever side calls `backend.run` uses the same circuit;
  - an interpreter that turns raw counts (dict, any bit order) into the result dict, using an **explicit register mapping** (clbit 0 ← q0, clbit 1 ← q1). It reports `counts`, the shot total, the correlated fraction (00+11), and honest `facts` that name the backend;
  - if Python can reach `backend` in a JS project, a once-only guarded runner that refuses a second call within the process and raises a clear error the UI can show ("restart the run to verify again").
- **(b)** `test_qollab_job.py`:
  - an **endianness fixture**: hand-written raw count dicts with a known physical meaning, for example a circuit that does `X(q0)` only must read as q0=1, q1=0, checked through the interpreter. Also run that fixture through local `qiskit.providers.basic_provider.BasicSimulator` (Qollab's built-in simulator class) to prove the bit order on real Qiskit output;
  - the once-only guard;
  - a check that a malformed or empty counts input is a failure, never a silent pass.
- **(c)** `vault/Research/qollab-backend-from-js-projects.md` with sources for each question, linked from the Research hub (`node scripts/vault-hubs.mjs`). Clearly separate measured facts from docs from unknowns.
- **(d)** A short proposal for the platform lane, in your report, of the exact `main.js` call site if `backend.run` must live in JS. Platform owns `main.js`; do not edit it.

**WHAT HAS NOT WORKED.** Nothing on ECHO yet. The earlier org found:
- a plain Python call on an IonQ backend fails with an XHR `ConnectionError`;
- whether the IonQ simulator costs credits when signed out is unresolved (owner to check).

You **cannot** run anything on Qollab or IonQ; only the owner can. Never write that something ran there. Local results are "local BasicSimulator". Never hardcode a backend name.

**VAULT NOTES TO READ FIRST.**
- `vault/AGENTS.md`, `vault/Home.md`, `vault/Index.md`
- `vault/Research/qollab-platform-and-submission.md` (§1, §2, open questions)
- `.claude/rules/gate-independence.md`, `qollab-runtime.md`, `evidence-and-honesty.md`

**WHERE TO START.** Run `node scripts/where.mjs qollab_job --branches`. Then fetch the docs and read the spike. Write the endianness test first from hand-derived meaning and watch it fail. Use the venv at `/Users/udsy/PycharmProjects/Qollab-Hackathon-Quantum-Unlocked/.venv/bin`.

**HOW I WILL JUDGE IT.**
1. Every claim about the platform carries a URL or an artifact path.
2. The endianness fixture goes red if the interpreter reverses bit order. Run that sabotage and report it, along with a sabotage that removes the guard.
3. No hardcoded backend, no second-run path.
4. Facts strings are honest per §7.5.
5. Unknowns are listed as questions, not guessed.

**REPORT.** Write `lanes/quantum/reports/backend-job.md` with a checkpoint within 1 h. It opens with a **Vault check**, then: findings with sources, what was built, commands with exit codes, the sabotage table including nulls, the `main.js` proposal, and `## Questions for the owner`. Commit to your branch.
=== END AGENT ===

=== LEARN ===
Lane setup (consult 1): the worker model key is `opus` (org.json `worker_models`; `sonnet` also exists), and the lane's parallel cap is 2. The vision's §10.3 sets `isIndependentCloning` from the state name, and §10.5 is only a deferred-measurement check. Workers must derive cloning results from the computed state and must build a separate teleportation branch model (measurement bits → conditional state → X/Z → fidelity). The shared `ExperimentResult` schema belongs to the platform lane, so this lane only proposes it, in `vault/Design/experiment-result-contract.md`. Whether `backend` can be reached from Python in a JS/Qiskit project is unresolved and is being settled by research (backend-job worker) before anyone builds on an assumption.
=== END LEARN ===
