"""Independent circuit checks for impact-qollab (overseer, 2026-10-10). Run from inside impact-qollab/:
    PYTHONPATH=. python ../evidence/integration/verify_qaoa_circuits.py
Checks: Dicke-state prep gives the uniform k-hot superposition; the cost layer equals exp(-i*gamma*E(x)) up to a
global phase; the XY mixer keeps all probability on k-hot strings. Exit 1 on any failure."""
import sys
from math import comb
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector
import qctrade.qaoa as q

bad = 0
def check(label, ok):
    global bad
    print(f"  {'ok  ' if ok else 'FAIL'} {label}")
    bad += not ok

for n, k in [(4, 2), (6, 2), (6, 3), (5, 1), (6, 5)]:
    qc = QuantumCircuit(n); q.dicke_state(qc, n, k)
    p = Statevector(qc).probabilities(); w = q.hamming_weights(n)
    check(f"dicke n={n} k={k}: support is exactly the k-hot strings, uniform 1/C(n,k)",
          np.allclose(p[w == k], 1 / comb(n, k)) and p[w != k].sum() < 1e-12)
rng = np.random.default_rng(1); n, k = 5, 2
Q = rng.normal(size=(n, n)); h, J = q.ising_from_qubo(Q); g = 0.37
qc = QuantumCircuit(n); q._cost_layer(qc, g, h, J)
d = np.diag(Operator(qc).data) * np.exp(1j * g * q.all_energies(Q))
check("cost layer = exp(-i gamma E) up to a global phase", np.allclose(d, d[0]))
c = q.build_qaoa(Q / np.abs(Q).max(), k, [0.3, 1.1, 0.7], [0.9, 0.2, 1.3], 'xy', False)
check("XY mixer (3 layers, random angles): no probability leaves the k-hot subspace",
      Statevector(c).probabilities()[q.hamming_weights(n) != k].sum() < 1e-12)
c = q.build_qaoa(Q / np.abs(Q).max(), k, [0.3], [0.9], 'x', False)
check("control: the X mixer DOES leave the k-hot subspace (the check can fail)",
      Statevector(c).probabilities()[q.hamming_weights(n) != k].sum() > 0.1)
print("VERIFY-QAOA-CIRCUITS", "FAIL" if bad else "PASS")
sys.exit(1 if bad else 0)
