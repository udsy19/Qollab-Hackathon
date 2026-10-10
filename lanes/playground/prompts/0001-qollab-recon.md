# Rules for every worker agent (read before your brief)

You are a Claude Code agent directed by the supervisor of lane `playground`. Read `/Users/udsy/agent-org/lanes/playground/context.md`
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
- **Images the supervisor should see** go in `/Users/udsy/agent-org/lanes/playground/renders/<your agent name>/` (PNG, descriptive
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

You are agent `qollab-recon` in worktree `/Users/udsy/agent-org/lanes/playground/wt/qollab-recon` on branch `lane/playground/qollab-recon`.

**GOAL:** Find out exactly how a project on Qollab (qollab.xyz) is built, published and run, with the IonQ simulator path in particular. The aim is that every idea we pitch and build is one a judge can run by pressing Run on Qollab, with no friction.

**VISION:** We are trying to win the Qollab x IonQ hackathon, Quantum Playground theme. Judges open our Qollab page and press Run. If the project's shape does not fit how Qollab runs code, we lose no matter how good the idea is.

**WHAT WE ARE BUILDING:** A Qiskit project in `playground/` (not picked yet) that is playful, artistic or unexpected. It must run on Qollab's free simulators, including IonQ's. It must be MIT-licensed and have a project page.

**WHAT HAS NOT WORKED:** Nothing has been tried yet. Do not guess the platform from general Qiskit knowledge: a guess here is the failure mode. Every fact needs a source URL or a screenshot.

**Vault notes to read first:**
- `vault/AGENTS.md`
- `vault/Home.md`
- `vault/Missions/qollab-ionq-hackathon-2026.md`
- `.claude/rules/hackathon-eligibility.md`
- `vault/Design/lanes-and-supervisors.md` (section "Where research findings go")
- `vault/Index.md`

Check whether `vault/Research/` already holds a Qollab platform note, possibly from the unlocked lane, which researches the same thing. If one exists, extend it. Do not write a second note.

**Questions to answer, each with a source:**
1. **Project format.** Is a Qollab project a Jupyter notebook, a Python script, a repo import, or something else? How does a published project page look, and what does "Run" do?
2. **Runtime.** Which Python version? Which packages are preinstalled (qiskit version, qiskit-aer, qiskit-ionq, matplotlib, numpy, ipywidgets, IPython.display Audio/HTML)? Can a project `pip install` extra packages?
3. **IonQ simulator.** How is it reached: through a `qiskit-ionq` provider, a Qollab-native backend, or a built-in key? Does it need the user's own IonQ API key? Find any limits on qubits, shots, queue time and noise models (e.g. `ionq_simulator` with `noise_model="aria-1"`). Does it cost anything? Spend is forbidden: free simulators only.
4. **Other free simulators** on Qollab, and how a project selects one.
5. **Output.** What can a run display: plots, images, audio, animations, HTML, interactive widgets, text? Is network access allowed at runtime? Are there time or memory limits?
6. **Examples.** Look at 3–5 existing public Qollab projects and the "Programming your first quantum circuits" lessons. Note their structure, what made the good ones engaging, and screenshot them.
7. **Hackathon specifics.** The Quantum Playground theme text, the judging criteria, the submission form fields, and the rules on pre-existing code.

**Where to start:** qollab.xyz, its FAQ, its lessons and the hackathon page. Use the defuddle skill or WebFetch for reading, and a headless browser (puppeteer) for screenshots of pages and projects. Do not sign up for anything, enter any card, or use the owner's accounts. If something can only be seen while logged in, say so and name exactly what is hidden. Do not install anything globally.

**What to deliver:**
- `vault/Research/qollab-platform.md`, linked from its hub. Run `node scripts/vault-hubs.mjs` and `python3 scripts/gen-subject-index.py`. The note answers each question above with source URLs, says "UNKNOWN — <why>" where it cannot, and has a short section titled "Constraints that shape a Playground idea", e.g. "audio playback: yes/no" or "interactive widgets: yes/no".
- Screenshots under `renders/playground/qollab-recon/`, with a README.

Commit on your branch.

**How I will judge it:** I will check that every answer has a source and that the screenshots match the claims. "UNKNOWN" is acceptable when it is honest and scoped. A confident claim without a source is a reject.

**Report:** Write `reports/` as instructed by the harness. It must open with a **Vault check** and carry a TL;DR that lists the constraints. Write a checkpoint report within 1 h even if research is unfinished. Target finishing within 75 min.

**Write your report to `/Users/udsy/agent-org/lanes/playground/reports/0001-qollab-recon.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/playground/renders/qollab-recon/` (PNG; only images newer than its last consult are shown to it).
