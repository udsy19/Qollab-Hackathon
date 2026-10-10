=== PLAN ===
**Lane goal:** Win the Quantum Playground theme (playful, artistic or unexpected uses of quantum) with a Qiskit project that runs end-to-end on Qollab's free simulators, including IonQ's. It must be MIT-licensed and live in `playground/`. Proof is screenshots of real runs. The owner publishes.

**Approach (phases)**
1. **Research + ideation (now, in parallel).**
   - `qollab-recon` (research only) finds out how a Qollab project is shaped and run: format (notebook or script), runtime, which packages are preinstalled, how the IonQ simulator is reached (a key or not, `qiskit-ionq` or a native backend), output display (matplotlib, audio, HTML, widgets), network, time and shot limits, and what existing Qollab projects look like. It writes all of this to `vault/Research/qollab-platform.md`.
   - `playground-ideas` drafts 6–8 candidate ideas. For each one it runs a tiny proof-of-mechanism on local Aer, in a lane venv, so the pitch rests on a real artifact (an image, a sound, a printout) and not on a claim.
2. **Pitch (next consult or the one after).** When both reports are in, I filter to 3 distinct ideas against what the platform can actually do, then ASK_OWNER with one paragraph per idea and an image per idea.
3. **Build (after the owner picks).** One builder runs the core quantum engine plus the Qollab-shaped entry point. A second worker handles presentation and output (visual or audio). Then a runnability worker proves it on the Qollab-equivalent path, including the IonQ simulator, with screenshots.
4. **Hand-off.** Material goes to the deliverables lane (project page draft, demo beats). LAND to main only with real-run screenshots.

**Done:** nothing yet (first consult, 2026-10-10 00:49 UTC ≈ Oct 9 20:49 ET).

**Timeline targets (ET)**
- Pitch out by about Oct 10 02:00.
- Owner pick.
- Runnable MVP by Oct 10 18:00.
- IonQ-sim proven by Oct 11 03:00.
- Runnable no later than Oct 11 07:00, which is the org-wide target.

**Risks**
- How Qollab runs projects is unknown. Ideas that need audio, interactivity or long runs may be impossible there, which is why research runs before the pitch is final.
- The IonQ simulator path may need an API key, which is the owner's account. If so, that becomes an ASK_OWNER.
- Qiskit or qiskit-ionq may not work on Python 3.13. Workers use a venv and record the versions.
- The unlocked lane may research the same platform. The research note is first-writer-wins and the other lane extends it, so neither forks it.
- The host is shared with the owner, so workers keep CPU light: small circuits and few shots locally.
=== END PLAN ===

=== AGENT name=qollab-recon model=sonnet base=lane/playground/integration ===
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
=== END AGENT ===

=== AGENT name=playground-ideas model=opus base=lane/playground/integration ===
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
=== END AGENT ===

=== LEARN ===
Consult 1 (2026-10-10 00:49 UTC): the pitch to the owner waits on two things. The first is platform research (how Qollab runs code and how the IonQ simulator is reached). The second is idea spikes, each with a real artifact. A pitch built on guesses about the runtime risks the owner picking an idea that cannot run when a judge presses Run on Qollab. Platform facts live in `vault/Research/qollab-platform.md`, shared with the unlocked lane: whoever writes it first owns it, and the other lane extends it.
=== END LEARN ===
