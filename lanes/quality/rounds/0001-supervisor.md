=== PLAN ===
**Lane goal:** A judge who presses Run on Qollab gets both projects running end-to-end on the free simulators, IonQ's included, with no friction. We prove it with logs and screenshots from the real path, and land fixes on main only with run proof.

**Where we are (consult 1, 2026-10-10 00:49 UTC / 2026-10-09 20:49 ET):** The repo has only the org layer. There is no project code yet and no ideas have been picked (the project lanes pitch first). Nobody knows yet how Qollab executes a project. Qiskit is not installed on the host. The host runs Python 3.13.

**Approach, in order:**
1. **Know the target (now).** Research how Qollab runs a project: file format (notebook? script? repo?), runtime and Python version, preinstalled packages, whether `pip install` is allowed, network limits, how the IonQ simulator is reached (qiskit-ionq plus an API key? a Qollab-provided backend? a local IonQ-like noise model?), run-time limits, and what a judge sees after pressing Run. Output: `vault/Research/qollab-execution.md`.
2. **Know our toolchain (now, in parallel).** Build a clean-env compatibility matrix on this host: Python 3.13 (and the Qollab Python version once known) × current qiskit / qiskit-aer / qiskit-ionq. Find out which IonQ simulator paths work with no API key and with a free key, and record install time and wall time for a canonical Bell + GHZ circuit. Output: `vault/Reports/` note + a reusable clean-env run recipe (one script, in a quality-owned path, after where.mjs search).
3. **Smoke harness (after 1+2).** One command that takes a project dir, creates a throwaway venv that mirrors Qollab's runtime, installs exactly what the project declares, runs it on Aer and on the IonQ simulator path, and saves logs + output images + timing under `evidence/quality/`. It goes red when an import is missing, a dependency is undeclared, the run is too slow, or IonQ is unreachable. Write it first and watch it fail on a deliberately broken toy project.
4. **Run the real projects (once playground/unlocked have code, ~Oct 10).** Run the harness on each lane branch, file defects back to the owning lane with reproductions, and fix only through the owning lane (or a quality branch they accept). Repeat at each project lane merge.
5. **Final proof (by 2026-10-11 07:00 ET).** Clean-env runs of main for both projects, plus screenshots of the Qollab-equivalent path. The owner publishes; afterwards we verify the published page if the owner gives us the link.

**Done:** nothing yet.
**Next:** workers `qollab-exec-research` and `toolchain-compat` (dispatched below).

**Risks:**
- The IonQ simulator may need an IonQ account/API key, and only the owner can create one. If so, ASK_OWNER once the research confirms it; meanwhile prove everything on Aer + the IonQ path that needs no key.
- Qollab's runtime may pin an older Qiskit, or block pip. Projects must then target that version, and we must tell the project lanes early.
- Python 3.13 wheels may lag for qiskit-ionq/aer. Use the Qollab-matching Python via `uv`/pyenv if available, without installing anything globally.
- Host is shared with the owner: workers keep venvs local and use one install at a time.
=== END PLAN ===

=== AGENT name=qollab-exec-research model=opus ===
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
=== END AGENT ===

=== AGENT name=toolchain-compat model=opus ===
**GOAL:** Prove which Qiskit toolchain actually installs and runs cleanly on this host, from an empty venv, on both Qiskit Aer and the IonQ simulator path. The project lanes then start from a known-good, pinned set instead of discovering breakage at 3 a.m.

**VISION:** This serves the hackathon mission (`vault/Missions/qollab-ionq-hackathon-2026.md`): projects that run when a judge presses Run on Qollab, on free simulators including IonQ's, with no friction.

**WHAT WE ARE BUILDING:** Two Qiskit projects, built by the playground and unlocked lanes. Quality (you) owns runnability. Another worker is researching Qollab's runtime in parallel. It will write `vault/Research/qollab-execution.md`; read it if it appears while you work, and add its Python/Qiskit versions to your matrix.

**WHAT HAS NOT WORKED:** Nothing has been tried yet. Known risks:
- The host has Python 3.13, and qiskit-aer/qiskit-ionq wheels may lag behind it.
- qiskit-ionq's `ionq_simulator` is a cloud API that may require an IonQ API key.
- Installing anything globally is forbidden.
- The host is the owner's Mac and is shared: one install at a time, venvs inside your worktree, and no touching processes that aren't ours.

**Vault notes to read first:** `vault/AGENTS.md`, `vault/Home.md`, `vault/Index.md`, `vault/Map-code.md`, `.claude/rules/hackathon-eligibility.md`, `.claude/rules/gate-independence.md` (laws 3, 7, 13), `.claude/rules/no-bloat.md` (run `node scripts/where.mjs` before writing any script).

**Do:**
1. Matrix: Python 3.13 (host), plus 3.11/3.12 if obtainable without a global install (e.g. `uv python install` into a local dir, or skip and name the skip). Cross it with the latest qiskit, qiskit-aer and qiskit-ionq. For each cell record: install success, install time, exact resolved versions (`pip freeze`), and import success.
2. Canonical circuits: a Bell pair and a 5-qubit GHZ, transpiled and run with 1024 shots on (a) AerSimulator and (b) the IonQ simulator via qiskit-ionq with **no** API key, recording the exact error. If a key-free path exists (local IonQ noise model, Qollab-provided backend), test that. Do not obtain or ask for a key; never print or commit a secret. Record counts, wall time, and a saved histogram PNG per run.
3. Write a small clean-env runner in a quality-owned path (e.g. `quality/clean-run.sh` or `scripts/quality/`, after the where.mjs search): `<project dir>` → throwaway venv → install the project's declared deps only → run its entry point under a timeout → logs, outputs and timings to `evidence/quality/<project>/<timestamp>/`. Exit codes follow the law: 0 green, 1 red, 2 refused, and a timeout reported as a HANG, never as red or green.
4. Prove the runner bites, and write the failing case first: a toy project with an undeclared import must go red; a toy that sleeps past the timeout must report HANG; the Bell toy must go green. Keep the toys under `quality/fixtures/`.

**Deliver:**
- `vault/Reports/toolchain-compat-2026-10-09.md`: the matrix, pinned recommended versions, the IonQ simulator finding, timings, and a "Recommended pins for project lanes" block.
- `vault/Research/clean-env-run-recipe.md`: how to run any project clean, with the exact commands.
- The runner and the fixtures, with evidence under `evidence/quality/toolchain/` (logs, histograms, a README).
- Hubs and index regenerated. Everything committed on your branch.

**How I will judge it:** I will rerun your runner on the three fixtures myself (from the logs you name). Each verdict must match. The histograms must show ~50/50 for Bell and 00000/11111 for GHZ. Every version is copied from `pip freeze` output, not typed by hand. Skips are named.

**Report:** open with a **Vault check**, then a TL;DR (the recommended pins and the IonQ verdict), the evidence paths with their exit codes, and the nulls (what you sabotaged that did not go red). Checkpoint within 1 h (PARTIAL if not done).
=== END AGENT ===

=== LEARN ===
Consult 1 (2026-10-10 00:49 UTC): the lane started from zero. There is no project code and the Qollab runtime is unknown. The first two moves are research into Qollab execution and a host toolchain matrix with a clean-env runner. Project-specific runs wait until the playground/unlocked lanes have code. Expected blocker: the qiskit-ionq `ionq_simulator` may need an IonQ API key that only the owner can create. Do not ask the owner until the research confirms whether Qollab provides a key-free IonQ path.
=== END LEARN ===
