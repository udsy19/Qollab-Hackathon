#!/usr/bin/env python3
"""Gate for impact-qollab/: does the Qollab project run, send exactly ONE backend job, and report the truth?

    python scripts/gates/impact-qollab-run.py            (needs qiskit>=2.5.2,<3 and scipy in the interpreter)

Checks, each against a value computed HERE, independently of the code under test:
  1. Dicke-state preparation gives the uniform superposition over k-hot strings (n = 2..8, every k).
  2. The QUBO -> Ising cost layer applies exp(-i gamma x'Qx) up to a global phase (random Q).
  3. main() run with a backend that behaves like an IonQ backend on Qollab (a second run() raises) makes
     exactly ONE run() call, for (n,k) in a small grid, and the call carries 2 circuits.
  4. The reported optimum equals a brute force over all 2^n bitstrings with sum = k (written here, not imported),
     every reported QUBO energy equals x'Qx of its reported selection, and the XY mixer's samples are all feasible.
  5. The console warns that the numbers are SYNTHETIC.
  6. At least one checked gap is non-zero, so check 4 is not vacuous.
Exit 0 pass, 1 fail, 2 missing input (qiskit/scipy absent, project folder absent): never a skip.
CEILING: this runs CPython locally on Qiskit's BasicSimulator. It does not prove the project runs in Pyodide on
Qollab, nor on IonQ's simulator; those need a real run on Qollab.
"""
import contextlib
import io
import os
import sys
from math import comb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT = os.path.join(ROOT, "impact-qollab")
if not os.path.isfile(os.path.join(PROJECT, "main.py")):
    print(f"IMPACT-QOLLAB-RUN REFUSED: no {PROJECT}/main.py")
    sys.exit(2)
try:
    import numpy as np
    from qiskit import QuantumCircuit
    from qiskit.providers.basic_provider import BasicSimulator
    from qiskit.quantum_info import Operator, Statevector
except ImportError as err:
    print(f"IMPACT-QOLLAB-RUN REFUSED: missing input {err}")
    sys.exit(2)

os.chdir(PROJECT)  # Qollab's working directory is the project root
sys.path.insert(0, PROJECT)
import main as project  # noqa: E402
from qctrade import qaoa as qa  # noqa: E402
from qctrade.instance import load_stats, select_universe  # noqa: E402
from qctrade.solvers import OptConfig, qubo_matrix  # noqa: E402

fails = []


def check(label, ok, detail=""):
    print(f"  {'ok  ' if ok else 'FAIL'} {label}" + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        fails.append(label)


# 1. Dicke states
bad = []
for n in range(2, 9):
    for k in range(1, n):
        qc = QuantumCircuit(n)
        qa.dicke_state(qc, n, k)
        p = Statevector(qc).probabilities()
        weight = np.array([bin(i).count("1") for i in range(1 << n)])
        if not np.allclose(p, (weight == k) / comb(n, k), atol=1e-9):
            bad.append((n, k))
check("Dicke |D(n,k)> exact for n=2..8, all k", not bad, f"wrong for {bad[:5]}")

# 2. Cost layer phases
rng = np.random.default_rng(11)
Q = rng.normal(size=(5, 5))
h, J = qa.ising_from_qubo(Q)
qc = QuantumCircuit(5)
qa._cost_layer(qc, 0.37, h, J)
diag = np.diag(Operator(qc).data)
E = np.array([[(i >> a) & 1 for a in range(5)] for i in range(32)], float)
E = np.einsum("si,ij,sj->s", E, Q, E)
ratio = diag / np.exp(-1j * 0.37 * E)
check("cost layer = exp(-i gamma x'Qx) up to global phase", np.allclose(ratio, ratio[0], atol=1e-9))


# 3-5. Full runs with an IonQ-like backend
class OneJobBackend:
    """Delegates to BasicSimulator; like Qollab on IonQ, a second run() in one run is an error."""
    def __init__(self):
        self.inner, self.calls, self.circuits = BasicSimulator(), 0, 0

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def run(self, circuits, **kw):
        self.calls += 1
        if self.calls > 1:
            raise RuntimeError("only one job is allowed per code run")
        self.circuits = len(circuits) if isinstance(circuits, (list, tuple)) else 1
        return self.inner.run(circuits, **kw)


def brute_force_opt(Q, k):
    n = len(Q)
    best, best_e = None, np.inf
    for i in range(1 << n):
        x = np.array([(i >> a) & 1 for a in range(n)], float)
        if x.sum() == k and x @ Q @ x < best_e:
            best, best_e = np.flatnonzero(x), float(x @ Q @ x)
    return best, best_e


nonzero_gaps = 0
# (8, 4, 16): so few shots that a QAOA row misses the optimum, so the gap check is tested on a NON-zero gap
for n, k, shots in [(6, 2, 512), (6, 3, 512), (5, 2, 512), (8, 4, 512), (8, 4, 16)]:
    be = OneJobBackend()
    project.backend = be
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            summary = project.main(n_assets=n, k=k, reps=2, shots=shots, seed=3, risk_aversion=6.0)
    except Exception as err:  # a second job, or anything else, is a failure
        check(f"n={n} k={k}: main() completes", False, f"{type(err).__name__}: {err}")
        continue
    text = out.getvalue()
    check(f"n={n} k={k}: exactly ONE backend.run call", be.calls == 1, f"{be.calls} calls")
    check(f"n={n} k={k}: the one job carries both QAOA circuits", be.circuits == 2, f"{be.circuits} circuits")
    stats, _ = load_stats(project.STATS_FILE)
    _, mu, cov = select_universe(stats, n)
    Qi = qubo_matrix(mu, cov, np.zeros(n), OptConfig(k=k, risk_aversion=6.0))
    opt_sel, opt_e = brute_force_opt(Qi, k)
    rows = {r["solver"]: r for r in summary["results"]}
    exact = rows["exact enumeration"]
    check(f"n={n} k={k}: reported exact optimum = independent brute force",
          list(exact["sel"]) == list(opt_sel), f"{exact['sel']} vs {opt_sel}")
    wrong_e = [s for s, r in rows.items() if r.get("sel") is not None and r.get("energy") is not None
               and abs(r["energy"] - float(np.eye(n)[list(r["sel"])].sum(0) @ Qi @ np.eye(n)[list(r["sel"])].sum(0))) > 1e-12]
    check(f"n={n} k={k}: every reported energy = x'Qx of its selection", not wrong_e, f"{wrong_e}")
    wrong_gap = [s for s, r in rows.items() if r.get("gap") is not None and abs(r["gap"] - (r["energy"] - opt_e)) > 1e-12]
    check(f"n={n} k={k}: every reported gap = E - E(brute force)", not wrong_gap, f"{wrong_gap}")
    nonzero_gaps += sum(1 for r in rows.values() if r.get("gap") is not None and r["energy"] - opt_e > 1e-9)
    check(f"n={n} k={k}: XY-mixer samples all feasible", rows["QAOA XY mixer"]["feasible_frac"] == 1.0,
          f"{rows['QAOA XY mixer']['feasible_frac']}")
    check(f"n={n} k={k}: console warns the numbers are SYNTHETIC", "These numbers are SYNTHETIC" in text)

check("at least one NON-zero gap was checked (else the gap check is vacuous)", nonzero_gaps > 0, "every row hit the optimum")

print("IMPACT-QOLLAB-RUN " + (f"FAIL ({len(fails)})" if fails else "PASS"))
sys.exit(1 if fails else 0)
