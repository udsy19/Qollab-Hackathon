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