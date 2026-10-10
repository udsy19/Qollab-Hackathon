# Rules for every worker agent (read before your brief)

You are a Claude Code agent directed by the supervisor of lane `unlocked`. Read `/Users/udsy/agent-org/lanes/unlocked/context.md`
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
- **Images the supervisor should see** go in `/Users/udsy/agent-org/lanes/unlocked/renders/<your agent name>/` (PNG, descriptive
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

You are agent `ionq-sim-spike` in worktree `/Users/udsy/agent-org/lanes/unlocked/wt/ionq-sim-spike` on branch `lane/unlocked/ionq-sim-spike`.

**GOAL:** Prove, with command output, that this host can build and run a Qiskit circuit on (a) a local Aer simulator and (b) IonQ's quantum simulator, with no money spent. Find out exactly what the IonQ path needs: package versions, the API key or account, and the noise models.

**VISION:** This serves the Quantum Unlocked project for the Qollab x IonQ hackathon. It must run on IonQ's free simulator. Every idea we pitch depends on knowing whether the IonQ path works and what it costs in friction.

**WHAT WE ARE BUILDING:** One interactive Qiskit project in `unlocked/`. The idea is not picked yet. Your job is the plumbing it will stand on.

**WHAT HAS NOT WORKED:** This is the first build, so nothing has been tried yet. Qiskit is not installed on the host. Python 3.13 is on the host, and qiskit and qiskit-ionq compatibility with it is unverified. Never install globally.

**Hard rules:**
- **Free simulators only.** Never submit to a QPU backend; only `ionq_simulator` or a local simulator. If any step needs a card, a paid plan or an account the owner must create, STOP and report it. Do not sign up for anything.
- Never print or commit a secret. If an IonQ key is needed, report that it is needed. The owner types secrets themselves.
- Keep CPU and RAM light; this machine is shared with the owner.

**Vault notes to read first:** `vault/AGENTS.md`, `vault/Home.md`, `vault/Index.md`, `.claude/rules/hackathon-eligibility.md`, and anything in `vault/Research/` about Qollab or IonQ (the playground lane may have written something).

**Steps:**
1. Create `unlocked/.venv`, gitignored, using `python3 -m venv`. Install qiskit, qiskit-aer and qiskit-ionq. Record the exact versions and any Python 3.13 failures. If 3.13 breaks, say what works instead.
2. Run a Bell-state circuit on Aer and save the counts and a histogram PNG.
3. Run the same circuit through qiskit-ionq's `ionq_simulator`. Cover the ideal case and noise model `aria-1` if possible. If a key is needed and absent, capture the exact error and find out from IonQ docs how a free key is obtained and whether it costs anything. Also find out whether Qollab supplies IonQ access itself. Check `vault/Research/` and the qiskit-ionq docs, and cite them.
4. Measure the wall-clock time per IonQ simulator job. Interactive ideas depend on latency.

**Deliver:**
- `unlocked/spike/` with the minimal scripts (kept small; it will be reused or deleted at build time).
- `evidence/unlocked/ionq-spike/` with the counts, histograms, logs, a version list and a README.
- `vault/Research/ionq-simulator-access.md`, sourced and linked from the hub.
- Commit everything on your branch.

**How I will judge it:** real command output and real images, not claims. A clear yes or no on "IonQ simulator reachable without spend", with what blocks it if no. Latency numbers with how they were measured.

**Report:** write `reports/ionq-sim-spike.md`. It opens with a **Vault check**, then a TL;DR, then evidence paths and exact commands with exit codes. Write a checkpoint within 1 h, marked PARTIAL if needed.

**Write your report to `/Users/udsy/agent-org/lanes/unlocked/reports/0001-ionq-sim-spike.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/unlocked/renders/ionq-sim-spike/` (PNG; only images newer than its last consult are shown to it).
