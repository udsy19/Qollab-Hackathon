# Rules for every worker agent (read before your brief)

You are a Claude Code agent directed by the supervisor of lane `ux`. Read `/Users/udsy/agent-org/lanes/ux/context.md`
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
- **Images the supervisor should see** go in `/Users/udsy/agent-org/lanes/ux/renders/<your agent name>/` (PNG, descriptive
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

You are agent `qollab-render-research` in worktree `/Users/udsy/agent-org/lanes/ux/wt/qollab-render-research` on branch `lane/ux/qollab-render-research`.

**GOAL:** Know exactly what a hackathon judge sees on Qollab after pressing Run, so that every presentation decision in this lane is built on fact, not guesswork.

**VISION:** Both projects should win on looks and clarity in the first seconds after Run, and in a 2–3 min demo video. That is only possible if we design for what Qollab can actually display.

**WHAT WE ARE BUILDING:** Two Qiskit projects for the Qollab x IonQ hackathon. Playground is playful or artistic; Unlocked makes a hard quantum idea click. Both are published on Qollab and run on its free simulators, including IonQ's. Ideas are not picked yet. Your output feeds the ux lane (presentation) and every other lane.

**WHAT HAS NOT WORKED:** Nothing has been tried yet; this is the first build. Org-wide failures to avoid:
- judging the wrong artifact
- making claims without evidence
- doing meta-work instead of product work

How Qollab runs projects is recorded nowhere yet. Another lane may be researching it right now.

**Vault notes to read first:**
- `vault/AGENTS.md`, `vault/Home.md`
- `vault/Index.md`
- `vault/Missions/qollab-ionq-hackathon-2026.md`
- `vault/Design/lanes-and-supervisors.md` (§ "Where research findings go")
- **everything under `vault/Research/`**. If another lane has already written a Qollab runtime note, EXTEND that note with a presentation section rather than writing a second one, and say so in your report.

**Questions to answer, each with a source URL or a screenshot:**
1. Project format on Qollab: Jupyter notebook, Python script, or something else? What happens visually when a judge presses Run?
2. Output rendering:
   - inline matplotlib (static PNG? `%matplotlib widget`?)
   - Qiskit's own visualisations (`circuit.draw('mpl')`, `plot_histogram`, `plot_bloch_multivector`, `plot_state_qsphere`)
   - ipywidgets and sliders
   - matplotlib animations, HTML/JS output, GIF/video embeds
   - plotly
   - which of these render, and which are blank or blocked?
3. Theme: is the background dark or light, and how wide is the output cell? What does that imply for figure size and colours?
4. IonQ simulator on Qollab: how jobs are submitted, typical wait time, and shot limits. These shape the demo pacing.
5. Available packages: preinstalled versions of qiskit, matplotlib and others. Can extra packages be pip-installed? Network limits?
6. Project page: what it can contain (images, GIFs, embedded video, markdown).

**Where to start:**
- qollab.xyz: its FAQ, the hackathon page, and the lessons "Programming your first quantum circuits".
- Published example projects on Qollab: screenshot one or two showing rendered output, if this is possible without sign-in.
- Never create accounts, never sign in, never spend money.

**Deliver:**
- `vault/Research/qollab-presentation-capabilities.md` (or a section in an existing Qollab runtime note), with sources and a "what this means for presentation" list of 5–10 concrete do/don't lines.
- Any screenshots under `renders/ux/qollab-research/`.
- Hub regenerated with `node scripts/vault-hubs.mjs`.
- Committed on your branch.

Where a question cannot be answered without signing in, mark it **UNKNOWN — needs owner account** and stop. Do not guess.

**How I will judge it:**
- every capability claim carries a source link or a screenshot
- unknowns are named as unknowns
- the do/don't list is specific enough that a visuals worker can act on it without re-researching

**Report:** `reports/qollab-render-research.md`. It opens with a **Vault check** (notes read, what was known, what you reused, what is stale), then a TL;DR, findings, unknowns and the paths of the evidence. Write a checkpoint report within 1 h even if research is incomplete.

**Write your report to `/Users/udsy/agent-org/lanes/ux/reports/0001-qollab-render-research.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/ux/renders/qollab-render-research/` (PNG; only images newer than its last consult are shown to it).
