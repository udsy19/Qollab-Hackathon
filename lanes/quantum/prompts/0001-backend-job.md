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

You are agent `backend-job` in worktree `/Users/udsy/agent-org/lanes/quantum/wt/backend-job` on branch `lane/quantum/backend-job`.

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

**Write your report to `/Users/udsy/agent-org/lanes/quantum/reports/0001-backend-job.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/quantum/renders/backend-job/` (PNG; only images newer than its last consult are shown to it).
