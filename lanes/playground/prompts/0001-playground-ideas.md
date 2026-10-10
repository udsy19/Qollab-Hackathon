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

You are agent `playground-ideas` in worktree `/Users/udsy/agent-org/lanes/playground/wt/playground-ideas` on branch `lane/playground/playground-ideas`.

**GOAL:** Produce 6–8 candidate project ideas for the Quantum Playground theme (playful, artistic or unexpected uses of quantum). Each one must be backed by a tiny working proof that the quantum mechanism does real work. From these I will pitch the owner 3 distinct ideas.

**VISION:** Win the theme in the Qollab x IonQ hackathon. Judges score four things equally: novelty & creativity, technical execution, impact potential and documentation quality. They judge by pressing Run on Qollab and looking at the result. The winner makes a judge smile in the first 10 seconds, and the quantum part is essential to it, not decoration. If you can swap in `random.random()` and the project is unchanged, the idea fails.

**WHAT WE ARE BUILDING:** A Qiskit project in `playground/`. It must run on Qollab's free simulators, including IonQ's simulator (possibly with IonQ noise models such as aria-1). It must be MIT-licensed, built in the 48 h window (ending 2026-10-11 19:00 ET) and come with a 2–3 min demo video. A parallel worker, `qollab-recon`, is researching how Qollab runs projects and will write `vault/Research/qollab-platform.md`. Read it if it appears while you work. Until then, assume a Jupyter-notebook-style environment with matplotlib, no guaranteed audio or widgets, and modest qubit counts (≤ ~20 qubits, a few thousand shots).

**WHAT HAS NOT WORKED / TRAPS:**
- Nothing has been tried yet.
- Known clichés that judges will have seen many times score low on novelty unless they have a real twist: a quantum coin flip or dice, a generic "quantum random art", quantum tic-tac-toe, a Bloch-sphere animation on its own.
- Ideas whose quantum part is only an RNG.
- Ideas that need hardware, paid QPU time, or more than about 25 qubits.
- Ideas that only work interactively, if Qollab turns out not to support that.

**Directions worth exploring** (not a limit; surprise me):
- Interference and entanglement as an artistic medium. Examples: music where chords are measurement statistics of evolving circuits; a generative textile or weave pattern from Grover or QFT amplitudes; Hamiltonian evolution as animation.
- IonQ's noise model used as a creative instrument, e.g. "the same art, ideal vs aria-1 noise".
- Games where superposition or entanglement changes the rules in a way only quantum allows.
- Quantum versions of playful classics where the quantum version behaves visibly differently: quantum walks drawing patterns, a "quantum Galton board", cellular automata.
- Unexpected domains: poetry, recipes, choreography, typography.

**What to do:**
1. Read the vault first: `vault/AGENTS.md`, `vault/Home.md`, `vault/Missions/qollab-ionq-hackathon-2026.md`, `.claude/rules/hackathon-eligibility.md`, `vault/Index.md`, and `vault/Research/` if it exists.
2. Create a venv inside your worktree: `python3 -m venv .venv && .venv/bin/pip install qiskit qiskit-aer qiskit-ionq matplotlib`. Record which versions work on Python 3.13. Never install globally, and keep `.venv` out of git. Light CPU only: this is the owner's Mac.
3. Brainstorm broadly. Then, for 6–8 ideas, write a ≤60-line proof-of-mechanism under `playground/_spikes/<idea>/`. Each proof runs a real circuit on Aer and produces the artifact a user would see: a PNG, a short WAV, or a printed board. Where possible, show the ideal vs noisy contrast, or show the classical-random version beside the quantum one so the difference is visible.
4. For each idea, write one paragraph covering:
   - what the user sees and does;
   - the quantum mechanism doing real work, and why classical randomness can't fake it;
   - why it scores on novelty, execution, impact and docs;
   - 48 h feasibility and the biggest risk;
   - the IonQ-simulator angle;
   - the path to its artifact.
5. Rank them, and recommend the 3 most distinct ones from each other.

**What to deliver:**
- `vault/Research/playground-idea-candidates.md`, linked from its hub. Run `node scripts/vault-hubs.mjs` and `python3 scripts/gen-subject-index.py`.
- The spikes, with their artifacts in `renders/playground/ideas/`, one image or audio file per idea.

Commit on your branch. The spikes are throwaway, so name them clearly as spikes.

**How I will judge it:** I will open every artifact. An idea with no artifact, or whose artifact looks no different from a classical RNG output, is dropped. I want distinct ideas, not three variants of one, and honest feasibility.

**Report:** It must open with a **Vault check**. The TL;DR is the ranked list with artifact paths. Write a checkpoint report within 1 h. Target finishing within 90 min.

**Write your report to `/Users/udsy/agent-org/lanes/playground/reports/0001-playground-ideas.md`, opening with `## TL;DR` (at most 10 lines).** Images the supervisor should see go in `/Users/udsy/agent-org/lanes/playground/renders/playground-ideas/` (PNG; only images newer than its last consult are shown to it).
