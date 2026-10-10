
## Consult 2 (2026-10-10 00:55 UTC)
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
