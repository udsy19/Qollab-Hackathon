=== PLAN ===
**Lane goal:** Win Quantum Unlocked. Build one interactive Qiskit project, in `unlocked/`, that makes a hard quantum idea click. It must run end to end on Qollab's free simulators, IonQ's simulator included, and real-run screenshots must prove it.

**Approach (phased):**
1. **Research (now, in parallel):**
   - (a) How Qollab projects look and run: format, runtime, packages, IonQ simulator access, limits, what judges see when they press Run. Also the best existing "quantum explained" projects, so our idea is new.
   - (b) Feasibility spike: a project venv on the host's Python 3.13 with qiskit and qiskit-ionq. Can the IonQ *simulator* be reached for free, and does it need an API key? This decides which interaction models are possible.
2. **Pitch (next consult, once 1a and 1b report):** three distinct ideas via ASK_OWNER. Each pitch gives the hard idea, how the user interacts so it clicks, why judges would score it high on all four traits, the 48 h feasibility, and the IonQ path. Until the owner picks, no build work.
3. **Build (after the pick):** a vertical slice first. That is the smallest end-to-end run on Qollab's path, with a screenshot of an IonQ simulator result. Then the interaction, the visuals and the explanatory narrative. Target is runnable by 2026-10-11 07:00 ET, then polish and handoff to the ux, quality and deliverables lanes.

**Done:** nothing yet. The org was set up on 2026-10-09.

**Next:** dispatch `qollab-recon` and `ionq-sim-spike`.

**Risks:**
- The Qollab runtime is unknown. It may be a notebook, a script or a web app, and it may block widgets or network access. This decides everything about the interaction model.
- The IonQ simulator may need an API key or account that only the owner can provide. If so, that becomes an owner question.
- Qiskit or qiskit-ionq may not work on Python 3.13.
- The playground lane is researching Qollab at the same time. Workers check `vault/Research/` first and do not duplicate it.
- The owner's pick latency eats into the 48 h window, so the pitch has to come early and be crisp.
=== END PLAN ===

=== AGENT name=qollab-recon model=opus base=lane/unlocked/integration ===
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
=== END AGENT ===

=== AGENT name=ionq-sim-spike model=opus base=lane/unlocked/integration ===
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
=== END AGENT ===

=== LEARN ===
Consult 1 (2026-10-10 00:49 UTC): the lane started with no prior work. The supervisor chose to research before pitching. Qollab's runtime format and IonQ simulator access decide which interaction designs are possible. Pitching before knowing them risks the owner picking an idea that cannot run on Qollab. The pitch goes out as soon as `qollab-recon` and `ionq-sim-spike` report; this is to keep the owner's decision latency short.
=== END LEARN ===
