"""QAOA for the k-of-n portfolio QUBO, built as Qiskit circuits.

Two variants, both from QC-TRADE's NumPy prototypes, rebuilt here as Qiskit circuits:

* X mixer   - |+>^n start, cost layer from the QUBO PLUS a cardinality penalty lam*(sum x - k)^2, RX mixer.
              Infeasible bitstrings (sum x != k) can be sampled; they are counted and discarded.
* XY mixer  - Dicke-state start |D(n,k)> (every k-hot string, equal weight), cost layer from the QUBO alone,
              a ring of XX+YY gates that swaps 01 <-> 10 and so never changes the number of 1s. Every
              ideal sample is feasible by construction.

The angles are tuned on this machine with Qiskit's `Statevector` (an exact classical simulation, no
backend jobs). Only the final, tuned circuits go to `backend.run`, all in ONE call (see main.py).
Bit order: qubit i is asset i; Qiskit prints bitstrings with qubit 0 on the RIGHT.
"""
from __future__ import annotations

from math import acos, sqrt
from time import perf_counter

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import XXPlusYYGate
from qiskit.quantum_info import Statevector
from scipy.optimize import minimize


def ising_from_qubo(Q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """E(x) = x'Qx with x_i = (1 - z_i)/2  ->  const + sum h_i z_i + sum_{i<j} J_ij z_i z_j. Returns (h, J upper)."""
    S = (Q + Q.T) / 2  # x'Qx = x'Sx
    off = S - np.diag(np.diag(S))
    h = -np.diag(S) / 2 - off.sum(axis=1) / 2
    J = np.triu(S, 1) / 2  # 2 S_ij x_i x_j, and x_i x_j contributes z_i z_j / 4
    return h, J


def penalised_qubo(Q: np.ndarray, k: int) -> tuple[np.ndarray, float]:
    """Q + lam*(sum x - k)^2 without its constant lam*k^2. lam = 4*sum|Q| as in QC-TRADE (certifies the feasible optimum is the ground state)."""
    lam = max(4 * float(np.abs(Q).sum()), 1e-4)
    Qp = Q + lam * np.ones_like(Q)
    Qp[np.diag_indices(len(Q))] -= 2 * k * lam
    return Qp, lam


def all_energies(Q: np.ndarray) -> np.ndarray:
    """x'Qx for every bitstring, indexed as Qiskit indexes statevector amplitudes (bit i of the index = qubit i)."""
    n = len(Q)
    states = np.arange(1 << n)
    bits = ((states[:, None] >> np.arange(n)) & 1).astype(float)
    return np.einsum('si,ij,sj->s', bits, Q, bits)


def hamming_weights(n: int) -> np.ndarray:
    states = np.arange(1 << n)
    return ((states[:, None] >> np.arange(n)) & 1).sum(axis=1)


def dicke_state(qc: QuantumCircuit, n: int, k: int) -> None:
    """Prepare |D(n,k)> on qubits 0..n-1 (Baertschi & Eidenbenz 2019, 'Deterministic preparation of Dicke states').

    Start from k ones, then apply split-and-cyclic-shift blocks SCS(m, min(k, m-1)) for m = n..2.
    Paper qubit p (1-based, left to right) is Qiskit qubit p-1. O(nk) gates, no ancillas.
    """
    for q in range(n - k, n):
        qc.x(q)
    for m in range(n, 1, -1):
        _scs(qc, m, min(k, m - 1))


def _scs(qc: QuantumCircuit, m: int, l: int) -> None:
    last = m - 1  # paper qubit m
    # two-qubit block on paper qubits (m-1, m)
    qc.cx(last - 1, last)
    qc.cry(2 * acos(sqrt(1 / m)), last, last - 1)
    qc.cx(last - 1, last)
    # three-qubit blocks on paper qubits (m-i, m-i+1, m), i = 2..l
    for i in range(2, l + 1):
        tgt, mid = last - i, last - i + 1
        qc.cx(tgt, last)
        _ccry(qc, 2 * acos(sqrt(i / m)), last, mid, tgt)
        qc.cx(tgt, last)


def _ccry(qc: QuantumCircuit, theta: float, c1: int, c2: int, tgt: int) -> None:
    """Doubly controlled RY from two Toffolis: X RY(-t/2) X RY(t/2) = RY(t) when both controls are 1, identity otherwise."""
    qc.ry(theta / 2, tgt)
    qc.ccx(c1, c2, tgt)
    qc.ry(-theta / 2, tgt)
    qc.ccx(c1, c2, tgt)


def _cost_layer(qc: QuantumCircuit, gamma: float, h: np.ndarray, J: np.ndarray) -> None:
    """exp(-i gamma H_C) with H_C = sum h_i Z_i + sum J_ij Z_i Z_j  ->  RZ(2 gamma h_i), RZZ(2 gamma J_ij)."""
    n = len(h)
    for i in range(n):
        if abs(h[i]) > 1e-15:
            qc.rz(2 * gamma * h[i], i)
    for i in range(n):
        for j in range(i + 1, n):
            if abs(J[i, j]) > 1e-15:
                qc.rzz(2 * gamma * J[i, j], i, j)


def ring_edges(n: int) -> list[tuple[int, int]]:
    return [(0, 1)] if n == 2 else [(j, (j + 1) % n) for j in range(n)]


def build_qaoa(Q_scaled: np.ndarray, k: int, gammas, betas, mixer: str, measure: bool) -> QuantumCircuit:
    """One QAOA circuit with the given angles. `Q_scaled` is the (already penalised, if X) QUBO divided by its scale."""
    n = len(Q_scaled)
    h, J = ising_from_qubo(Q_scaled)
    qc = QuantumCircuit(n, name=f'qaoa_{mixer}')
    if mixer == 'x':
        qc.h(range(n))
    elif mixer == 'xy':
        dicke_state(qc, n, k)
    else:
        raise ValueError(f'unknown mixer {mixer!r}')
    for gamma, beta in zip(gammas, betas):
        _cost_layer(qc, float(gamma), h, J)
        if mixer == 'x':
            qc.rx(2 * float(beta), range(n))  # exp(-i beta X) on every qubit
        else:
            for i, j in ring_edges(n):  # exp(-i beta (XX+YY)/2): cos(beta) - i sin(beta) on the {01,10} pair
                qc.append(XXPlusYYGate(2 * float(beta)), [i, j])
    if measure:
        qc.measure_all()
    return qc


def tune_angles(Q: np.ndarray, k: int, mixer: str, reps: int, maxiter: int, starts: int, seed: int) -> dict:
    """Minimise the exact expected (scaled) energy <psi|H_C|psi> over the 2*reps angles with COBYLA, from `starts` seeded random starts.

    The energy is scaled by the spread of the energies the mixer can reach (all strings for X, k-hot strings
    for XY), as QC-TRADE did, so one angle range suits every instance. Uses Statevector only: no backend job.
    """
    t0 = perf_counter()
    n = len(Q)
    feasible = hamming_weights(n) == k
    if mixer == 'x':
        Qm, lam = penalised_qubo(Q, k)
        spread = all_energies(Qm).std()
    else:
        Qm, lam = Q, 0.0
        spread = all_energies(Q)[feasible].std()
    scale = max(float(spread), 1e-12)
    Qs = Qm / scale
    energies = all_energies(Qs)
    rng = np.random.default_rng(seed)
    evals = 0

    def expected(params) -> float:
        nonlocal evals
        evals += 1
        qc = build_qaoa(Qs, k, params[:reps], params[reps:], mixer, measure=False)
        return float(Statevector(qc).probabilities() @ energies)

    best = None
    for _ in range(starts):
        x0 = np.r_[rng.uniform(0, np.pi, reps), rng.uniform(0, np.pi / 2, reps)]
        fit = minimize(expected, x0, method='COBYLA', options={'maxiter': maxiter, 'rhobeg': 0.5})
        if best is None or fit.fun < best.fun:
            best = fit
    gammas, betas = best.x[:reps], best.x[reps:]
    probs = Statevector(build_qaoa(Qs, k, gammas, betas, mixer, measure=False)).probabilities()
    return {'mixer': mixer, 'Q_scaled': Qs, 'penalty': lam, 'scale': scale, 'gammas': gammas, 'betas': betas,
            'ideal_probs': probs, 'ideal_feasible_mass': float(probs[feasible].sum()), 'evaluations': evals,
            'tune_seconds': perf_counter() - t0}


def outcome_index(key: str) -> int:
    """A counts key as the integer whose bit i is qubit i: '0b..'/'0x..' or a bitstring with qubit 0 rightmost."""
    key = key.replace(' ', '')
    return int(key, 0) if key[:2] in ('0x', '0b') else int(key, 2)


def decode_counts(counts: dict, Q: np.ndarray, k: int) -> dict:
    """Read a sampled histogram: shots per outcome index, feasible-shot count, the best feasible sample by TRUE QUBO energy, the most frequent feasible string."""
    n = len(Q)
    by_index: dict[int, int] = {}
    for key, c in counts.items():
        idx = outcome_index(key) & ((1 << n) - 1)
        by_index[idx] = by_index.get(idx, 0) + int(c)
    shots = sum(by_index.values())
    feasible_shots, best, best_e, top, top_c = 0, None, np.inf, None, -1
    for idx, c in by_index.items():
        x = np.array([(idx >> i) & 1 for i in range(n)], float)
        if int(x.sum()) != k:
            continue
        feasible_shots += c
        e = float(x @ Q @ x)
        sel = np.flatnonzero(x)
        if e < best_e:
            best, best_e = sel, e
        if c > top_c:
            top, top_c = sel, c
    return {'shots': shots, 'by_index': by_index, 'feasible_shots': feasible_shots, 'best': best,
            'best_energy': best_e, 'most_frequent': top, 'most_frequent_count': top_c}
