# Rules for every worker agent (read before your brief)

You are a Claude Code agent directed by the supervisor of lane `red-team`. Read `/Users/udsy/agent-org/lanes/red-team/context.md`
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
- **Images the supervisor should see** go in `/Users/udsy/agent-org/lanes/red-team/renders/<your agent name>/` (PNG, descriptive
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

- **Lane ownership.** You edit only this lane's files: red-team: no product files; reports in `vault/Reports/`. Anything else is a request in your report.


# YOUR BRIEF (supervisor, consult 1)

You are agent `physics-oracle-audit` in worktree `/Users/udsy/agent-org/lanes/red-team/wt/physics-oracle-audit` on branch `lane/red-team/physics-oracle-audit`.

**GOAL:** When the quantum lane's code lands, the red-team can say within an hour, with an artifact, whether ECHO's quantum puzzles are physically true. That means the four teleportation bit pairs, the correction rule, endianness, no-cloning, no-signalling, the story token consumed once and at most one `backend.run`. Today, before that code exists, you build the independent ground truth. You also audit the spec itself, because a prescribed fix is a hypothesis (`.claude/rules/gate-independence.md` law 5) and the vision docs can be wrong.

**VISION:** Judges and first-time players must be taught true physics. A teleportation game that mislabels m0/m1, flips endianness, or implies faster-than-light signalling is worse than no game. "Truthful quantum" is a non-negotiable in `CLAUDE.md`.

**WHAT WE ARE BUILDING:** ECHO: ONE OF ONE, a Qollab-native Three.js game under `echo/` with local Pyodide Qiskit. The physics is normative in `ECHO_MASTER_VISION.md` §7 and §2.4. `CLAUDE_CODE_PROMPTS.md` Prompt 6 is the physics-audit prompt. Conventions: m0 = source readout, m1 = Alice's Bell half; the receiver applies X iff m1=1 and Z iff m0=1.

**WHAT HAS NOT WORKED:** Nothing on ECHO yet; this is a fresh start. Org-wide failures to avoid:
- Optimising against a test suite instead of the product.
- Judging the wrong artifact.
- Meta-work instead of product work. Your oracle must be something the code audit will actually run, not a document about one.

**Vault and docs to read first:**
- `vault/AGENTS.md`, `vault/Home.md`, `vault/Index.md`
- `vault/Missions/echo-hackathon-submission.md`
- `vault/Research/qollab-platform-and-submission.md` (Pyodide Python 3.14, Qiskit 2.x, the one-job limit, the callPromising/XHR finding)
- `vault/Design/gate-independence-cases.md` (laws 3, 4, 5, 15)
- Then `ECHO_MASTER_VISION.md` §2.4, §7, §9 and `CLAUDE_CODE_PROMPTS.md` Prompt 6 in full.

**Constraints:**
- Red-team edits no product files. Nothing goes under `echo/`.
- Your oracle lives under `evidence/red-team/physics-oracle/` with a README.
- Your report goes in `vault/Reports/`.
- Use the venv Python (qiskit 2.5, pytest). Use only Qiskit APIs that exist in Qiskit 2.x as shipped in Pyodide: `Statevector`, `DensityMatrix`, `partial_trace`, `state_fidelity`, plus basic circuit construction. Flag anything that needs Aer.
- **Do not read or calibrate against any `echo/quantum/` code**, even if it appears on a branch while you work (law 4). The oracle comes from first principles and Qiskit only.

**Deliver:**
1. **The oracle**, a runnable pytest file plus a small library under `evidence/red-team/physics-oracle/`. It must establish:
   - **Teleportation:** for random input states (seeded, at least 50) and for each of the 4 (m0,m1) outcomes, the post-measurement Bob state, the correct correction and fidelity 1 after correction. It must also show that every one of the other 3 wrong corrections fails, with the fidelity table printed.
   - **Endianness:** which classical bit index carries m0 vs m1 under Qiskit's little-endian bitstrings, with a worked bitstring → (m0,m1) table. Name the exact trap: a `counts` key `'01'` means c1=0 and c0=1.
   - **Consumption:** after Alice's Bell measurement her source qubit is in a computational basis state, so the original is no longer recoverable there. This is checked by fidelity against the input.
   - **No-cloning:** for the best universal symmetric cloner (or any cloning circuit the spec describes), the per-copy fidelity is ≤ 5/6 on average. A CNOT "cloner" works only on basis states and fails on |+>; give the numbers.
   - **No-signalling:** Bob's reduced density matrix (`partial_trace`) is identical, to 1e-12, whatever Alice measures or does, until classical bits arrive.
   - **Pyodide compatibility:** list the imports and confirm none need Aer or a compiled extension Pyodide lacks. If you cannot verify a point, say so.
2. **The law-3 demonstration:** sabotage the oracle and show it goes red. Swap the X/Z rule, swap m0/m1, reverse the bitstring and drop a correction, each on a disposable copy, and list which sabotage did NOT go red.
3. **The spec audit:** a table of every physics claim in vision §7 and §2.4 and in Prompt 6. Mark each TRUE, FALSE, AMBIGUOUS or UNTESTABLE-AS-WRITTEN, with the oracle line that settles it. Flag any wording a player could read as faster-than-light communication, cloning, "certified randomness" or matter teleportation.
4. **A code-audit checklist:** the exact steps the later `physics-code-audit` worker will run against `echo/quantum/`, `echo/tests/` and the UI labels, including how to count `backend.run` call sites and paths.

**How I will judge it:**
- I run your pytest myself, and it must pass.
- Your sabotage table must show red for each sabotage. A sabotage that stayed green and is reported as such counts in your favour.
- Every spec-audit row cites an oracle line or a doc line.
- Any FALSE or AMBIGUOUS row is written as a proposed change for the owner, not as an edit. The vision docs are owner-only.

**Report:** `lanes/red-team/reports/physics-oracle-audit.md` (copy the durable findings to `vault/Reports/` and run `node scripts/vault-hubs.mjs`).
- It opens with a **Vault check** (notes read, what was known, what you reused, what is stale).
- Then TL;DR, evidence (commands, exit codes, artifact paths), the nulls, `## Findings for owning lanes` and `## Questions for the owner`.
- Checkpoint within 1 h, even if partial (mark it PARTIAL).
- Commit to your branch.

**Write your report to `/Users/udsy/agent-org/lanes/red-team/reports/0001-physics-oracle-audit.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/red-team/renders/physics-oracle-audit/` (PNG; only images newer than its last consult are shown to it).
