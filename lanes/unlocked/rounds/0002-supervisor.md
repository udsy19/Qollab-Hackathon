=== PLAN ===
**Lane goal:** Win Quantum Unlocked. Build one interactive Qiskit project in `unlocked/` that makes a hard quantum idea click. It must run end to end on Qollab's free simulators, IonQ's included, with screenshots of real runs as proof.

**What we now know (consult 2, from evidence):**
- **Qollab project format** (recon screenshots 01–04, not yet the final report):
  - A project is "JS + Qiskit": a Project Card (What it shows / How it works / Make it yours), a Code tab, and a "Run on Qollab" button that renders an interactive HTML Preview in the page.
  - The official showcase is a JS interactive. Click qubits, syndrome lights, then a "storm mode" Monte Carlo running in the browser. At load, one anchor circuit runs on the selected backend.
  - So the winning shape is: the browser does the interactivity (instant), and one real Qiskit circuit runs on the chosen backend as the anchor.
- **Backends in the Select-QPU dialog** (screenshot 02):
  - Free and local: Built-in simulator (24q), AWS Braket local (25q), IBM noise-model simulators (8).
  - **IonQ Aria 1/2 and Forte 1/Forte Enterprise 1 are "Remotely Run Simulators", marked "Credits apply".** Picking one while signed out redirects to sign-in (screenshot 04).
  - This collides with "Free simulators only" plus the eligibility rule "runs on … IonQ's simulator". That needs an owner ruling (ASK below).
- **Local stack** (ionq-sim-spike, merged this consult): Py 3.13, qiskit 2.5.2, aer 0.17.2 and qiskit-ionq 1.1.1 all work. A Bell circuit on Aer gives 515/509, as shown in `renders/ionq-sim-spike/bell-aer-histogram.png`. Direct qiskit-ionq calls from a published project are impossible: Qollab allows GET only, forbids keys in published code, and IonQ sends no CORS header. So IonQ is reached only through Qollab's own backend picker, one circuit per run.
- **Novelty constraint:** the repetition-code QEC game is Qollab's own showcase. Any error-correction pitch must be clearly different from it, or be dropped.

**Approach:**
1. Research. Spike done; `qollab-recon` still running. I do not re-dispatch.
2. Pitch three ideas via ASK_OWNER as soon as recon reports. Each pitch is shaped as a browser interactive plus one anchor circuit that runs on the picked backend (IonQ when credits allow). Candidate seeds, to be checked against recon's prior-art list:
   - (a) interference / phase made visible, e.g. a Mach–Zehnder "phase knob" with Deutsch–Jozsa as the payoff;
   - (b) Grover as amplitude-sculpting you do by hand, racing the classical search;
   - (c) Bell / CHSH: "beat the classical 75%" as a game against a hidden-variable bot, with the quantum strategy confirmed on IonQ.
3. After the owner picks, build the vertical slice first: the project format on Qollab's Built-in simulator, then one IonQ simulator run. Target runnable by 2026-10-11 07:00 ET.

**Done:** ionq-sim-spike (merged). Its vault notes are `vault/Research/ionq-simulator-access.md` and `vault/Reports/ionq-sim-spike.md`.

**Next:** recon's report, then the pitch. In parallel, the owner answers the IonQ-credits question.

**Risks:**
- IonQ simulators may cost Qollab credits. Possible outcomes: the owner OKs free hackathon credits, or "Built-in/IBM free" counts as the IonQ path. Unresolved, this blocks eligibility rule 1.
- Every IonQ run needs sign-in, so judges pressing Run on IonQ hit friction. The default backend should be the free Built-in simulator, with IonQ as the documented second run.
- The Qollab runtime's Python/Qiskit versions are still unverified and need a signed-in run. The owner owns that account.
- Pick latency. The pitch has to go out the consult recon lands.
=== END PLAN ===

=== MERGE branch=lane/unlocked/ionq-sim-spike ===

=== ASK_OWNER ===
**IonQ simulators on Qollab show "Credits apply". How should we satisfy "runs on IonQ's simulator" under your "Free simulators only" rule?**

Evidence: [Select-QPU dialog](renders/qollab-recon/02-select-qpu-signed-out-ionq-credits-apply.png) · [IonQ pick → sign-in wall](renders/qollab-recon/04-signed-out-ionq-sim-redirects-to-sign-in.png)

- Qollab's Run dialog lists Built-in (24q), AWS Braket local and 8 IBM noise-model simulators as **Free**.
- IonQ Aria 1/2 and Forte 1/Forte Enterprise are listed under "Remotely Run Simulators" with **"Credits apply"**, and picking one requires sign-in.
- A published project cannot call IonQ directly: Qollab forbids API keys and POST requests.

Options:
1. **Your Qollab account has free or hackathon credits for the IonQ simulators.** We use a small number of them: one anchor circuit per run, a few test runs by you. The project defaults to the free Built-in simulator, so judges never need credits.
2. **Free backends only.** The project runs on Built-in/IBM, and the IonQ path is documented but not exercised by us. This may weaken eligibility.
3. You check with the hackathon organisers what "runs on IonQ's simulator" requires.

Recommendation: **option 1, if your account shows free credits.** Could you sign in to Qollab, open the Run dialog on any project, and tell us the credit balance and the cost per IonQ simulator run?

While you're signed in, please also run this in any Qollab Python cell and paste the output:
`import sys, qiskit; print(sys.version, qiskit.__version__)`

Three idea pitches for you to pick from follow shortly. Build work waits for your pick.
=== END ASK ===

=== LEARN ===
2026-10-10 consult 2: On Qollab, the IonQ simulators (Aria 1/2, Forte 1/Forte Enterprise 1) are "Remotely Run Simulators" with "Credits apply". They need sign-in, while Built-in, Braket-local and IBM simulators are Free. Evidence: renders/qollab-recon/02-*.png, 04-*.png. Never pick IonQ as a project's default backend: judges would hit a sign-in or credit wall. The default is the free Built-in simulator, and IonQ is the documented anchor run, pending the owner's credits ruling.
=== END LEARN ===

=== LEARN ===
2026-10-10 consult 2: The winning Qollab shape is "JS + Qiskit". It has a Project Card (What it shows / How it works / Make it yours), and Run renders an interactive HTML Preview. Interactivity runs in the browser, and one anchor circuit runs on the selected backend. Evidence: renders/qollab-recon/01-*.png, 03-*.png (Qollab's own repetition-code showcase). Every pitch and build follows this shape. A published project cannot call qiskit-ionq itself (GET-only, no keys, no CORS), per vault/Research/ionq-simulator-access.md.
=== END LEARN ===

=== LEARN ===
2026-10-10 consult 2: Novelty constraint: the distance-3 repetition-code QEC game (click to flip, syndrome, storm-mode threshold plot) is Qollab's own official showcase. A repetition-code or threshold pitch would read as a copy to judges. Error correction is only pitchable with a clearly different angle, e.g. phase-flip/Shor code or the surface code.
=== END LEARN ===
