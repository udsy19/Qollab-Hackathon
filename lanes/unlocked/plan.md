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