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

You are agent `qollab-recon` in worktree `/Users/udsy/agent-org/lanes/unlocked/wt/qollab-recon` on branch `lane/unlocked/qollab-recon`.

**GOAL:** Find out exactly how a Qollab project is built, published and run, and what judges see when they open one and press Run. Then survey the best existing "make quantum click" explainers, so the supervisor can pitch three ideas that are new and that fit Qollab's real runtime.

**VISION:** This serves the Qollab x IonQ hackathon, Quantum Unlocked theme ("make the hardest ideas in quantum computing click"). Judges score novelty, technical execution, impact and documentation by opening the Qollab page and pressing Run. An idea that cannot run in Qollab's format, or that copies a well-known demo, loses.

**WHAT WE ARE BUILDING:** One interactive Qiskit project in `unlocked/`. It is MIT-licensed, runs on Qollab's free simulators including IonQ's, and has a project page and a 2–3 min demo video. The idea is not picked yet. Your research feeds the pitch.

**WHAT HAS NOT WORKED:** This is the first build, so nothing has been tried yet. Two org-wide failures to avoid: claims without sources, and meta-work instead of product facts.

**Vault notes to read first:** `vault/AGENTS.md`, `vault/Home.md`, `vault/Index.md`, the mission `vault/Missions/qollab-ionq-hackathon-2026.md`, `.claude/rules/hackathon-eligibility.md`. Check `vault/Research/` **first**: the playground lane may already have written a Qollab note. If it has, read it, extend it and cite it. Do not duplicate it.

**Answer these with sources (URLs and quotes):**
1. **Project format.** What a Qollab project actually is: a notebook, a Python script, a multi-file repo or an embedded app? Which files does it need, and is there an entry point convention?
2. **Runtime.** Python and Qiskit versions, preinstalled packages, whether `pip install` works, and whether network access exists. Interactivity: do ipywidgets or matplotlib animations work? Can input be read from the user? Are there execution time and memory limits?
3. **Simulators.** Which free simulators Qollab exposes. How IonQ's simulator is reached from inside Qollab: the provider or backend name, whether a key is needed, whether Qollab injects credentials, and the shot or qubit limits. Include the noise-model options, such as IonQ's `aria-1` noise simulation.
4. **Project page.** Its fields, what a good one looks like, and how judges see it.
5. **Hackathon specifics.** The Quantum Unlocked theme text verbatim, the judging criteria, and the submission mechanics.
6. **Prior art.** 5–10 of the best existing educational quantum projects or explainers: Qollab's own featured projects, Quirk, IBM Quantum Composer, quantum-game style tools, and past hackathon winners. For each, say which hard idea it covers, how the user interacts with it, and what gap it leaves.

Start at qollab.xyz: the FAQ, the hackathon page, the "Programming your first quantum circuits" lessons and any public example projects. Look at IonQ's docs for the simulator and qiskit-ionq. You may use sub-agents for parallel web research.

**Deliver:**
- `vault/Research/qollab-platform.md`, or your extension of an existing note. It must give a "How a Qollab project runs" checklist that a builder can follow blind.
- `vault/Research/quantum-explainer-prior-art.md`.
- Both linked from the Research hub (`node scripts/vault-hubs.mjs`).
- Commit them on your branch.
- Write unknowns as unknowns, for example "could not confirm X; the evidence is Y". Never guess.

**How I will judge it:** every claim about Qollab has a source URL. The checklist is concrete enough to build to. The prior-art list shows clearly what is already done, so our pitch can avoid it.

**Report:** write `reports/qollab-recon.md` in the lane. It opens with a **Vault check**: notes read, what was known, what you reused, and what is stale. Then a TL;DR, then sources. Write a checkpoint within 1 h even if the work is partial, and mark it PARTIAL.

**Write your report to `/Users/udsy/agent-org/lanes/unlocked/reports/0001-qollab-recon.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/unlocked/renders/qollab-recon/` (PNG; only images newer than its last consult are shown to it).
