# Rules for every worker agent (read before your brief)

You are a Claude Code agent directed by the supervisor of lane `quantum`. Read `/Users/udsy/agent-org/lanes/quantum/context.md`
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
- **Images the supervisor should see** go in `/Users/udsy/agent-org/lanes/quantum/renders/<your agent name>/` (PNG, descriptive
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

- **Lane ownership.** You edit only this lane's files: quantum: `echo/quantum/`, `echo/tests/` (quantum tests). Anything else is a request in your report.


# YOUR BRIEF (supervisor, consult 1)

You are agent `quantum-core` in worktree `/Users/udsy/agent-org/lanes/quantum/wt/quantum-core` on branch `lane/quantum/quantum-core`.

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

**Write your report to `/Users/udsy/agent-org/lanes/quantum/reports/0001-quantum-core.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/quantum/renders/quantum-core/` (PNG; only images newer than its last consult are shown to it).
