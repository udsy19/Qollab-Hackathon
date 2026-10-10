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

You are agent `shared-contracts` in worktree `/Users/udsy/agent-org/lanes/platform/wt/shared-contracts` on branch `lane/platform/shared-contracts`.

**GOAL:** Every lane (gameplay, story-ui, quantum, art) can build tonight against one frozen, platform-owned definition of how the game talks to itself. They should not each invent state names, event names, terminal ids or result shapes that then fail to join at integration. A wrong name must fail loudly at the call site, not silently do nothing.

**VISION:** ECHO's quest is a deterministic state machine (vision §9) driven by named events (§9.3). Its physics results cross the JS↔Python bridge as typed results (§8.4), so that the UI never confuses simulator counts with exact probabilities and never shows invented numbers (CLAUDE.md "typed result schemas").

**WHAT WE ARE BUILDING:** A single platform-owned module, `echo/contracts.js`: plain ES module, named exports, no Node, no bundler. This location is provisional and is with the owner as a question, so keep it to one file that can move with one import change. It contains:
1. `QUEST_STATES` (vision §9.1, verbatim) and `TRANSITIONS` (the §9.2 table), frozen, plus a pure `transition(state, event)` that returns `{ok, state, reason}`.
2. `EVENTS`: world/quest event names for the §9.3 consequences and the bus. Derive these from the vision; do not make them up beyond it, and list any you had to add with a reason.
3. `INTERACTABLE_IDS`: from §9.4 plus the rooftop terminal and clone booth as the vision names them.
4. `ENGINE_KINDS` and `validateExperimentResult(obj)`. The validator is a guarded check of the §8.4 shape. It rejects: unknown engine; probabilities that don't sum to 1±1e-9; `counts` present under engine `exact_qiskit_local`; `measurementBits` outside {0,1}; missing `facts`. It returns a list of errors, never throws silently.
5. A short `echo/CONTRACTS.md` for the other lanes. It covers the exact Python dict shape the quantum lane's functions must return (plain serialisable values only; m0 = source readout, m1 = Alice's Bell half; X iff m1=1, Z iff m0=1), and how to propose a change (through platform only).

**WHAT HAS NOT WORKED:** Nothing tried on ECHO yet. The project-wide failure modes are optimising against tests instead of the product, and building behind flags nobody switches on.

**Read first:**
- `vault/AGENTS.md` and `vault/Index.md`
- vision §8.2, §8.4, §8.7 and §9 (all of it)
- §10.x wherever it shows adapter or state code
- `CLAUDE.md` (code conventions)
- `.claude/rules/lane-ownership.md`, `.claude/rules/no-bloat.md`

Run `node scripts/where.mjs ExperimentResult --branches` and `git grep -n "QUEST_STATES\|transition("` first.

**Checks you derive and write FIRST, watched red:** a small Node test under `tools/contract-check/` (Node is fine outside `echo/`).
- It replays the full happy path TITLE→CREDITS through `transition`.
- It proves every state in §9.1 is reachable. Derive the expected set from the vision text, not from your own table (law 8).
- It proves invalid events are refused.
- It runs the validator against good and bad fixtures.

**Sabotage round:** delete a transition, misspell a state, flip the probability tolerance. Report which ones went red and which (the nulls) did not.

**Also prove it loads in a browser:** a throwaway page in `tools/` that imports `echo/contracts.js` as an ES module and prints the happy-path trace, plus a screenshot.

**How I will judge:**
- The red-then-green log.
- The sabotage nulls.
- The browser screenshot.
- Whether `CONTRACTS.md` is enough for the quantum lane to write `formats.py` without asking.

**Report** goes in `/Users/udsy/agent-org/lanes/platform/reports/`:
- Open with a "Vault check".
- Then: TL;DR, decisions you made that the vision did not settle (each one becomes an owner question), commands with exit codes, evidence paths, and `## Questions for the owner`.
- Checkpoint within 1 h.

**Write your report to `/Users/udsy/agent-org/lanes/platform/reports/0001-shared-contracts.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/platform/renders/shared-contracts/` (PNG; only images newer than its last consult are shown to it).
