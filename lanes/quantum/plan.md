**Lane goal (G1, due Sat 2026-10-10 04:00 ET; plan row 4).** Build `echo/quantum/{__init__,cloning,entanglement,teleportation,formats,qollab_job}.py` to match vision §7 and §10.3–10.7. Every function returns JSON-safe dicts for the JS bridge (`callPromising(...).toJs()`). Tests go in `echo/tests/` and cover:
- basis states copy; |+>, |−> and phase states do not (reduced purity 0.5, and the output is not ψ⊗ψ);
- receiver marginal stays 50/50 for sender I/X/Z (partial_trace gives I/2), and I vs X shows a joint-correlation difference;
- teleportation for 6+ states × all 4 branches at fidelity ≥ 0.999999, plus the "no corrections" average that is independent of the source;
- an endianness fixture;
- the deferred-measurement circuit labelled as a verification, not a link;
- the one selected-backend Bell verification.

**Approach: two workers in parallel (cap 2), with no file overlap.**
1. `quantum-core` owns `cloning.py`, `entanglement.py`, `teleportation.py`, `formats.py`, `__init__.py`, `tests/test_{cloning,entanglement,teleportation}.py`, and the proposed `ExperimentResult` contract note in the vault.
2. `backend-job` owns `qollab_job.py`, `tests/test_qollab_job.py` (endianness fixture and counts parsing), and a research note on how a JS/Qiskit project reaches `backend`: from JS (§10.7) or from a Python module. It also checks whether our Qiskit calls run under Pyodide (Py 3.14, qiskit ≥2.5.2). It uses the §8.4 field names verbatim so `formats.py` can absorb them when I merge.

**Contract with the platform lane.** Platform owns the shared `ExperimentResult` schema. We propose it as `vault/Design/experiment-result-contract.md` (status: proposed), taking vision §8.4 verbatim and adding fields only with a stated reason. Platform rules on it. Likely split: `backend.run` lives in `main.js`, which platform owns. Quantum supplies the circuit spec and the counts→result interpretation.

**Done:** nothing yet. Fresh start; no `echo/` directory exists.

**Next:** judge both reports. Merge core first, then backend-job, reconciling it onto `formats.py`. Then send a red-team or reviewer pass covering:
- gate independence: expected values come from hand-derived amplitudes, not from the code under test;
- a sabotage round: swap the m0/m1 correction mapping, drop the H, flip endianness. Each must turn the tests red.

Then a Pyodide smoke test through the local runner, coordinated with the platform lane.

**Risks:**
- Pyodide's Qiskit API may differ from local qiskit 2.5.
- Ambiguity over whether `backend` is reachable from Python in JS projects.
- Bitstring endianness.
- Schema drift with platform.
- Over-claiming: never say "ran on IonQ/Qollab" without the owner's confirmation.