# Rules for every worker agent (read before your brief)

You are a Claude Code agent directed by the supervisor of lane `quality`. Read `/Users/udsy/agent-org/lanes/quality/context.md`
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
    `.claude/rules/`); a hook refuses it and a landing gate re-checks it. To change one, file
    `node scripts/propose.mjs --row <id> --kind … --why "…"` and say so in your report.
  - No auto-memory: no `memory:` frontmatter, no `.claude/agent-memory/` (per-branch copies conflict).
- **Builds.** Use your own build dir (already set in your env). Heavy builds go through the machine-wide
  queue (it is on your PATH). Build only what you need.
- **Sub-agents.** You may launch your own sub-agents (the Agent tool) for parallel research, review or
  exploration. Give each a goal-framed brief, and merge their findings into YOUR report. You are
  accountable for them. Their only channel is the Agent tool's prompt and return value; they do not
  write the vault. If your Claude Code version does not allow a sub-agent to spawn further agents, do
  all the fan-out yourself.
- **Images the supervisor should see** go in `/Users/udsy/agent-org/lanes/quality/renders/<your agent name>/` (PNG, descriptive
  names). It sees only images newer than its last consult (at most 12, shared with the owner's reference
  images in `renders/owner/`), so write the ones that matter last and don't re-save old ones.
- **Never print or commit secrets.**
- **CHECKPOINT REPORT.** You have a fixed time budget. Write your report file within the first hour, then
  update it at least every 2 hours. Each update covers state, commits, evidence and next. The final version
  replaces it. Never let more than 2 hours of findings exist only in your head.
- **REPORT** (to the path at the end of your brief). The supervisor sees its `## TL;DR`, its first ~2k
  characters and its last ~3k, so the shape matters:
  - `## TL;DR` FIRST, at most 10 lines: outcome, evidence paths, what you recommend;
  - Vault check;
  - what you found;
  - what you changed (commits);
  - evidence paths;
  - what you did NOT do or could not verify;
  - what the supervisor should do next (LAST, so it is in the tail the supervisor reads).


# YOUR BRIEF (supervisor, consult 1)

You are agent `qollab-exec-research` in worktree `/Users/udsy/agent-org/lanes/quality/wt/qollab-exec-research` on branch `lane/quality/qollab-exec-research`.

**GOAL:** Establish exactly how Qollab executes a published project when a hackathon judge presses Run, so that both of our projects are built to run there first time with no friction.

**VISION:** This serves the hackathon mission (`vault/Missions/qollab-ionq-hackathon-2026.md`). The rules are hard: Qiskit on Qollab's free simulators including IonQ's, runnable on Qollab as published, deadline 2026-10-11 19:00 ET. If a judge presses Run and it fails, we lose regardless of how good the idea is.

**WHAT WE ARE BUILDING:** Two Qiskit projects (Quantum Playground, Quantum Unlocked), built by other lanes. The quality lane (you) keeps them runnable. Your output is the reference every lane will build against.

**WHAT HAS NOT WORKED:** Nothing has been tried yet. This is the first research. Known traps: guessing the runtime from general Qiskit docs instead of Qollab's own; assuming the IonQ simulator needs no key; and believing a marketing page over the actual lesson/notebook interface.

**Vault notes to read first:** `vault/AGENTS.md`, `vault/Home.md`, `vault/Index.md`, `vault/Missions/qollab-ionq-hackathon-2026.md`, `vault/Design/lanes-and-supervisors.md#Where research findings go`, `.claude/rules/hackathon-eligibility.md`. Check `vault/Research/` in case another lane already wrote this. If they did, verify it and extend it rather than duplicating.

**Where to start:** qollab.xyz (FAQ, hackathon page, rules, "Programming your first quantum circuits" lessons, any docs and example projects), the hackathon announcement/Discord/Devpost if public, and IonQ's docs for qiskit-ionq and the IonQ simulator (`ionq_simulator`, noise models, API key requirements, free tier). Read only. Do not sign up, log in, create accounts or submit anything: those actions are the owner's. If a fact needs an account to see, say so and list exactly what the owner would need to check.

**Answer each of these with a cited source (URL + quote) or the word UNKNOWN:**
1. Project format on Qollab: notebook (.ipynb), .py script, repo import from GitHub, or something else. Entry point conventions.
2. Runtime: Python version, Qiskit version(s) preinstalled, other preinstalled packages; whether `pip install` / requirements.txt is honoured.
3. Execution: browser (Pyodide/JupyterLite) or server kernel? Time, memory and network limits? Can it fetch from the internet?
4. Simulators offered, and exactly how code selects the IonQ simulator (backend name, provider import, whether an API key is needed and who supplies it, whether a noise model like `aria-1` is free).
5. What a judge sees: outputs (plots, images, text, widgets?), and whether interactive input works.
6. Project page: fields and format, and how the MIT licence and disclosure of prior code are shown.
7. Anything in the hackathon rules that constrains runnability (e.g. "must run in under N minutes").

**Deliver:** `vault/Research/qollab-execution.md` (frontmatter as the vault contract requires, a Sources list, one section per question above, and a "Consequences for our projects" section: concrete do/don't rules for project lanes). Link it from the Research hub (`node scripts/vault-hubs.mjs`) and regenerate the index (`python3 scripts/gen-subject-index.py`). Commit on your branch.

**How I will judge it:**
- Every claim carries a URL and a quote. UNKNOWNs are named, not papered over.
- The "Consequences" rules are specific enough that a project lane could follow them blind.
- Where screenshots of Qollab pages are possible without logging in, save them under `evidence/quality/qollab-research/` and reference them.

**Report:** `reports/` per your role. Open with a **Vault check**. Give a TL;DR of the seven answers, then list what is UNKNOWN and exactly what the owner would have to look at to resolve it. Checkpoint report within 1 h, even if partial (mark it PARTIAL).

**Write your report to `/Users/udsy/agent-org/lanes/quality/reports/0001-qollab-exec-research.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/quality/renders/qollab-exec-research/` (PNG; only images newer than its last consult are shown to it).
