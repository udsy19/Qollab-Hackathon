# ionq-sim-spike — report (FINAL, 2026-10-09)

## TL;DR
- **Aer: YES.** A Bell circuit runs on local Aer under Python 3.13.12 (qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ionq 1.1.1). 3/3 runs exit 0, results are only `00`/`11` at ~50/50, each job takes 1–7 ms and the whole process 0.6–1.1 s. Histogram: `renders/ionq-sim-spike/bell-aer-histogram.png`.
- **IonQ simulator reachable without spend: YES in principle; NOT exercised from this host.** The simulator is free and unlimited, but submitting needs an IonQ API key (free account). This host has none, and I signed up for nothing. Without a key, the provider, `get_backend("ionq_simulator")` and transpile all succeed; `backend.run` fails with `IonQCredentialsError('Credentials `token` may not be None!')` (exit 1).
- **IonQ API status (no key):** `GET /v0.4/backends/simulator` returns 200, `available`, 29 qubits, queue 0. Noise models are `aria-1, aria-2, forte-1, forte-enterprise-1, ideal`. HTTP round-trip is 0.10–0.31 s. **Job latency is not measured** because there is no key.
- **The Qollab finding matters more than the key.**
  - Qollab's rules allow only GET requests to servers that permit cross-origin requests, and they forbid API keys in published code.
  - qiskit-ionq submits with POST, and `api.ionq.co` sends no CORS header for qollab.xyz.
  - So a published project cannot call qiskit-ionq itself. Qollab's runtime must supply the IonQ backend (inferred; see "not verified" below).
  - Qollab also says: "IonQ backends accept one per run". So one IonQ circuit per run.
- **Recommendation:** design the interactive part on the local simulator and give IonQ one "run it on IonQ" circuit. Next, someone with a Qollab account should run the primer and list Qollab's backends.

## Vault check
- **Read:** `vault/AGENTS.md`, `vault/Index.md`, `vault/Research/README.md` (empty), `vault/Design/lanes-and-supervisors.md` § Where research findings go, `vault/CLAUDE.md`, `.claude/rules/hackathon-eligibility.md`, `lanes/unlocked/context.md`.
- **Already known:** nothing about IonQ or Qollab access. `vault/Research/` was empty. `where.mjs bell --branches` exited 1 (nothing anywhere), and no `lane/*` branch differs from main.
- **Reused:** nothing (none existed).
- **Stale or wrong:** `context.md` and the brief say "Python 3.13 is on the host". Host `python3` is actually **3.14.6** (`/opt/homebrew/bin/python3`); 3.13.12 and 3.12 are also installed. I used `python3.13` explicitly. 3.14 also works: wheels exist for all three packages.

## What I found
| question | answer | evidence |
|---|---|---|
| versions | qiskit 2.5.2, qiskit-aer 0.17.2, qiskit-ionq 1.1.1, numpy 2.5.3, matplotlib 3.11.2 | `evidence/unlocked/ionq-spike/versions-py313.txt` |
| Python 3.13 failures | none; install exit 0 in ~7 s | `install-py313.log` |
| Python 3.14 | qiskit abi3, aer cp314 arm64 and ionq py3 wheels all exist | `py314-wheels.log` |
| key env var | `QISKIT_IONQ_API_TOKEN` > `IONQ_API_KEY` > `IONQ_API_TOKEN` (env or `.env`) | `qiskit_ionq/helpers.py:785-814` |
| key cost | simulator "unlimited and requires no credits" (OLCF); Azure "Free of cost"; key comes from a free IonQ Cloud account. **Card at signup: UNVERIFIED** | `vault/Research/ionq-simulator-access.md` |
| noise models | live list above; aria = legacy, ≤25 qubits; forte/ideal ≤29; `ideal` returns probabilities | `ionq-api-probe.log` |
| what the IonQ job would send | `{"backend":"simulator","noise":{"model":"aria-1"},"shots":1024,…}` built offline | `ionq-payload-offline.log` |
| does Qollab supply IonQ | its rules: projects "run on Qollab's free simulators, including IonQ's"; "IonQ backends accept one per run"; GET-only network; no keys | `qollab-page-excerpts.txt` |
| latency | Aer job 1–7 ms; IonQ API HTTP round-trip 0.10–0.31 s (9 curl samples); **IonQ job time not measured** | `run-aer.log`, `ionq-api-probe.log` |

## What I changed (commits)
- `fd373e9` on `lane/unlocked/ionq-sim-spike` (17 files, +371):
  - `unlocked/spike/bell.py`: one script with `aer` and `ionq [--noise]` modes. It writes counts JSON and a histogram PNG and records `submit_s` and `submit_to_result_s`. The only IonQ backend it can name is `ionq_simulator`.
  - `unlocked/.gitignore` (excludes `.venv/`).
  - `evidence/unlocked/ionq-spike/` (README lists the command and exit code for each file).
  - `vault/Research/ionq-simulator-access.md` (sourced) and `vault/Reports/ionq-sim-spike.md` (measured).
- Hubs not committed, per brief. `vault-hubs.mjs --check` shows Reports, Research and Map STALE (exit 1), so the loop must regenerate them.
- Side note: my researcher sub-agent ran `git merge --no-edit main` in this worktree. It was a fast-forward that added only `.claude/loop-prompts/org-tracker.md` (main's commit `7fdbee9`). No content from me was affected.

## Exact commands (exit codes)
- `/opt/homebrew/bin/python3.13 -m venv unlocked/.venv && unlocked/.venv/bin/pip install qiskit qiskit-aer qiskit-ionq matplotlib pylatexenc` → 0
- `MPLBACKEND=Agg unlocked/.venv/bin/python unlocked/spike/bell.py aer --out evidence/unlocked/ionq-spike` ×3 → 0, 0, 0
- `env -u IONQ_API_KEY -u QISKIT_IONQ_API_TOKEN -u IONQ_API_TOKEN … bell.py ionq [--noise aria-1]` → 1 (IonQCredentialsError at `bell.py:48`, `backend.run`)
- `curl https://api.ionq.co/v0.4/backends/simulator` → HTTP 200; `/v0.4/jobs` → HTTP 403

## Not done / not verified
- **No real IonQ simulator job ran:** there is no key, and I did not sign up (brief: owner's account). So I have no IonQ job latency, IonQ counts or IonQ histogram.
- **Card at IonQ signup:** UNVERIFIED. `identity.ionq.com` does not render without a browser.
- **Qollab's IonQ backend:** its name and API, whether `qiskit_ionq` is importable in Qollab's (likely Pyodide/WASM) runtime, and Qollab's Python/Qiskit versions are all UNVERIFIED. They need a Qollab login, which belongs to the owner.
- The "Qollab supplies IonQ" conclusion is **inferred** from the GET-only rule, the no-keys rule and the missing CORS header. It was not observed.

## What the supervisor should do next
1. **Ask the owner, or an agent the owner logs in for, to open Qollab's "Programming your first quantum circuits" primer** and run one cell: `import sys, qiskit; print(sys.version, qiskit.__version__)`, then list the backends the runtime offers. That settles how IonQ is accessed on the real path judges use. Without it, the project's IonQ step is unproven.
2. **Optional:** if the owner wants local IonQ numbers, they create a free IonQ Cloud account (checking whether it asks for a card), export `IONQ_API_KEY` in their own terminal, then run `unlocked/.venv/bin/python unlocked/spike/bell.py ionq --noise ideal --out evidence/unlocked/ionq-spike` and the same with `--noise aria-1`. Each run records its latency. The cost is $0 (simulator only).
3. **Design constraint for the idea pitch:** interactive loops run on the local simulator, which takes milliseconds. IonQ gets exactly one circuit per run, which means a "confirm on IonQ" button, not a slider.
