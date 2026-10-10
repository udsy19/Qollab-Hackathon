# Rules for every worker agent (read before your brief)

You are a Claude Code agent directed by the supervisor of lane `deliverables`. Read `/Users/udsy/agent-org/lanes/deliverables/context.md`
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
- **Images the supervisor should see** go in `/Users/udsy/agent-org/lanes/deliverables/renders/<your agent name>/` (PNG, descriptive
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

You are agent `qollab-page-research` in worktree `/Users/udsy/agent-org/lanes/deliverables/wt/qollab-page-research` on branch `lane/deliverables/qollab-page-research`.

**GOAL:** We need to know, with sources, exactly what a judge sees and does on Qollab, so our documentation is shaped for that surface and not for a generic GitHub repo. Find out four things:
- what a Qollab project page is: its fields, length limits, markdown and media support, how code and notebooks attach, how "Run" works, and the runtime (Python and Qiskit versions, available packages, network);
- how a project reaches IonQ's free simulator from Qollab (credentials and environment variables, or a built-in backend?);
- how submission works for the Qollab x IonQ hackathon (where the video link goes, required fields, disclosure of prior code);
- what the best existing Qollab projects and pages look like.

**VISION:** Documentation quality is a quarter of the score. The best docs in the hackathon are the ones that fit the platform the judges actually use, and that need zero friction to run.

**WHAT WE ARE BUILDING:** Two Qiskit projects (Playground theme, Unlocked theme) that run on Qollab's free simulators including IonQ's, each with an MIT licence, a Qollab project page and a 2–3 minute demo video. The deliverables lane writes the pages, READMEs and video scripts.

**WHAT HAS NOT WORKED:** Nothing has been tried yet. The project context does record that the Qollab runtime and format are unknown, and that guessing them is the risk.

**Vault first:** before you search, read:
- `vault/AGENTS.md`
- `vault/Home.md`
- `vault/Index.md`
- `vault/Missions/qollab-ionq-hackathon-2026.md`
- `.claude/rules/hackathon-eligibility.md`
- everything already in `vault/Research/`, since another lane may have written Qollab findings. If they have, extend their note instead of writing a second one (no-bloat).

**Where to start:**
- qollab.xyz: the FAQ, the hackathon page and its rules, the "Programming your first quantum circuits" lessons, and any public project pages.
- IonQ's docs on the qiskit-ionq simulator backend and free access.
- Use the defuddle skill to read pages. Read only: do not sign up, log in, submit, or create anything on any account. Owner accounts are the owner's.

**Deliver:**
1. `vault/Research/qollab-platform-and-submission.md`. Every claim carries its source URL and the date you read it. Mark as UNKNOWN anything you could not establish, and say what would settle it. If the owner needs to look at something while logged in, write it as a short question for them.
2. Inside that note, a section called "Implications for our docs". It lists the project-page fields we must fill and their limits, the exact run instructions a judge would follow, and what goes in the video versus the page.
3. Two or three exemplar Qollab project pages (or the closest equivalent hackathon pages). For each, a screenshot under `renders/deliverables/research/`, plus one line on what makes it good or weak.
4. A link from the Research hub (`node scripts/vault-hubs.mjs`).

**How I'll judge it:** I'll check that the sources are real and cited, that the unknowns are named rather than guessed, and that the screenshots exist. The real test is whether I can write the page template straight from your note.

**Report:** `reports/qollab-page-research.md`. It opens with a Vault check, then gives the TL;DR, the findings, the unknowns and the questions for the owner. Write a checkpoint report within 1 hour even if the work is partial, marked PARTIAL.

**Write your report to `/Users/udsy/agent-org/lanes/deliverables/reports/0001-qollab-page-research.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/deliverables/renders/qollab-page-research/` (PNG; only images newer than its last consult are shown to it).
