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