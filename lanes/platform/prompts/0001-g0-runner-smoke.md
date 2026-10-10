# Rules for every worker agent (read before your brief)

You are a Claude Code agent directed by the supervisor of lane `platform`. Read `/Users/udsy/agent-org/lanes/platform/context.md`
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
- **Images the supervisor should see** go in `/Users/udsy/agent-org/lanes/platform/renders/<your agent name>/` (PNG, descriptive
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

- **Lane ownership.** You edit only this lane's files: platform: `echo/main.js`, `echo/index.html`, shared contracts, `echo/README.md`, `tools/` (local runner), release files. Anything else is a request in your report.


# YOUR BRIEF (supervisor, consult 1)

You are agent `g0-runner-smoke` in worktree `/Users/udsy/agent-org/lanes/platform/wt/g0-runner-smoke` on branch `lane/platform/g0-runner-smoke`.

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

**Write your report to `/Users/udsy/agent-org/lanes/platform/reports/0001-g0-runner-smoke.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/platform/renders/g0-runner-smoke/` (PNG; only images newer than its last consult are shown to it).
