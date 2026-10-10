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

You are agent `docs-kit` in worktree `/Users/udsy/agent-org/lanes/deliverables/wt/docs-kit` on branch `lane/deliverables/docs-kit`.

**GOAL:** Build the documentation kit, so that the moment the owner picks the two ideas, a worker can produce a top-tier README, Qollab page draft and demo-video script for each project in a few hours, and nothing eligibility-critical is forgotten.

**VISION:** Documentation quality is a judged trait, and we want the best docs in the hackathon. Judges skim: in the first screen they should understand what the project does, why it's quantum, and how to press Run. The eligibility items (MIT licence, disclosure of prior and third-party code, run instructions for the free simulators including IonQ) must never depend on someone remembering them.

**WHAT WE ARE BUILDING:** Two Qiskit projects for the Qollab x IonQ hackathon, one in Quantum Playground (playful, artistic) and one in Quantum Unlocked (make hard quantum ideas click). The build window is 2026-10-09 19:00 ET to 2026-10-11 19:00 ET. The ideas aren't picked yet, so everything you write must be independent of the idea.

**WHAT HAS NOT WORKED:** Nothing has been tried yet. Org-wide failures to avoid:
- meta-work instead of product work: keep the kit lean, with no generators, no tooling and no gates beyond what's needed;
- claims the product doesn't support.

**Vault first:** read:
- `vault/AGENTS.md`
- `vault/Home.md`
- `vault/Index.md`
- `vault/Missions/qollab-ionq-hackathon-2026.md`
- `.claude/rules/hackathon-eligibility.md`
- `vault/Research/`

A parallel worker (`qollab-page-research`) is writing `vault/Research/qollab-platform-and-submission.md`. If it lands while you work, shape the Qollab page template to its field list. If it hasn't, leave clearly marked `<!-- TODO(qollab-format) -->` spots in the template; don't guess.

**Deliver** (only in `docs/`, the root `README.md` and the root `LICENSE`; do not create `playground/` or `unlocked/`, which belong to other lanes):
1. A root `LICENSE`: standard MIT text, `Copyright (c) 2026 Udaya Tejas`.
2. A root `README.md` skeleton: a one-line pitch of the repo and a card for each project, with placeholders for the name, one-line hook, hero image, Run on Qollab link and theme. It also covers: built for the Qollab x IonQ hackathon, free simulators only, the licence, and the disclosure.
3. `docs/templates/project-README.md`, structured in this order:
   - hook and hero image;
   - what you'll see;
   - the quantum idea in plain words, then precisely;
   - run it on Qollab (IonQ simulator) in three steps or fewer;
   - run it locally;
   - how it works (the circuit, with a diagram);
   - what's novel;
   - limits and honesty;
   - credits and disclosure;
   - licence.

   Include short guidance comments for whoever fills it in.
4. `docs/templates/qollab-page.md`: the project-page draft template.
5. `docs/templates/demo-video.md`: a 2–3 minute script and shot-list template. It's a timed table (timecode, shot, on-screen, voice-over, source: which real run or screenshot it comes from), with a hook in the first 10 seconds and the live run on the IonQ simulator shown on screen. The total must be timed at about 150 words per minute.
6. `docs/DISCLOSURE.md`: a ledger of prior and third-party code. It already names Qiskit, qiskit-ionq and the agent-org tooling layer. Find from git when the org layer was committed relative to the window, and state it as you find it. It has a table that the project lanes add rows to.
7. `docs/STYLE.md`: a one-page writing guide. Plain words, no unexplained jargon, every claim backed by a run, image alt text, consistent names.

**How I'll judge it:** I'll read each template as if I were filling it in for a made-up example project. If I'm left guessing anywhere, or an eligibility item can be skipped, it fails. Show this yourself: fill the README template for a toy example (a Bell-state "quantum coin") in `docs/templates/EXAMPLE-filled.md`, then render it with any markdown previewer or a headless browser and save a screenshot under `renders/deliverables/docs-kit/`. Keep the whole kit concise; templates that bloat get cut.

**Report:** `reports/docs-kit.md`. It opens with a Vault check, then gives the TL;DR, the files with their paths, the screenshot paths, and the open TODOs that wait on the Qollab research. Commit to your branch. Write a checkpoint within 1 hour.

**Write your report to `/Users/udsy/agent-org/lanes/deliverables/reports/0001-docs-kit.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/deliverables/renders/docs-kit/` (PNG; only images newer than its last consult are shown to it).
