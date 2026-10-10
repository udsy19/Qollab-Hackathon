"""QAOA for the k-hot portfolio-selection QUBO, built in Qiskit, simulated by Qiskit Aer.

CLASSICAL SIMULATION ONLY. Every number this module produces comes from an
ideal, noiseless statevector simulated on a CPU (qiskit-aer, method
'statevector'). It is not quantum hardware, it carries no noise, calibration or
queueing, and its runtime says nothing about the runtime of a quantum computer.

Two variants share one cost layer:

* ``mixer='x'``  standard QAOA: |+>^n start, RX mixer, cardinality enforced by
  a quadratic penalty P(sum x - k)^2 (P chosen by :func:`cardinality_penalty`,
  which provably keeps the penalised ground state k-hot), infeasible shots
  discarded at decoding.
* ``mixer='xy'`` cardinality-preserving QAOA: Dicke-state start |D(n,k)>
  prepared by the Baertschi-Eidenbenz circuit, ring of XX+YY mixers, so every
  amplitude stays in the k-hot subspace and no penalty is needed.

Cost layer: the QUBO E(x) = x'Qx is mapped exactly to an Ising Hamiltonian
(:func:`ising_from_qubo`) and divided by its uniform-superposition standard
deviation, so gamma has a comparable scale across instances. Decoding samples
``shots`` bitstrings with a seeded RNG from the exact output distribution and
keeps the feasible sample with the lowest TRUE QUBO energy x'Qx.
"""
from __future__ import annotations
from math import comb
from time import perf_counter
import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ParameterVector
from qiskit.circuit.library import XXPlusYYGate, RYGate
from qiskit_aer import AerSimulator

MAX_QAOA_QUBITS = 22  # 2^22 amplitudes = 64 MB; beyond this the per-evaluation time, not memory, is the wall


def cardinality_penalty(Q: np.ndarray) -> float:
    """Smallest penalty weight that provably keeps the penalised ground state k-hot.

    Flipping one bit changes x'Qx by at most r = max_i (|Q_ii| + 2 sum_{j!=i} |Q_ij|).
    A state with |x| = k + d reaches a k-hot state in |d| flips, so its energy is
    at least E* - |d| r; with the penalty P d^2 >= P |d| it is >= E* whenever P >= r.

    This is about 2n times smaller than the imported code's 4 sum|Q|, but it is still
    the dominant term of the cost Hamiltonian, so after normalisation the feasible
    energies get small phases and X-mixer QAOA leaks mass to infeasible strings
    (reported per run as 'qaoa_feasible_mass'). A smaller, heuristic P could leave the
    penalised optimum infeasible, i.e. change the objective; we keep the provable one.
    """
    A = np.abs(np.asarray(Q, float))
    r = float((A.diagonal() + 2 * (A.sum(axis=1) - A.diagonal())).max())
    return max(r, 1e-12)


def penalised_qubo(Q: np.ndarray, k: int, penalty: float) -> np.ndarray:
    """Q + P (1'x - k)^2 without the constant P k^2 (x binary, so x_i^2 = x_i)."""
    n = len(Q)
    Qp = np.asarray(Q, float) + penalty * np.ones((n, n))
    Qp[np.diag_indices(n)] -= 2 * k * penalty
    return Qp


def ising_from_qubo(Q: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    """x'Qx = c + sum_i h_i z_i + sum_{i<j} J_ij z_i z_j with x_i = (1 - z_i)/2.

    Returns (c, h, J) with J strictly upper triangular. Exact for every bitstring.
    """
    Q = (np.asarray(Q, float) + np.asarray(Q, float).T) / 2
    off = Q - np.diag(Q.diagonal())
    c = 0.5 * Q.diagonal().sum() + 0.5 * np.triu(off, 1).sum()
    h = -0.5 * Q.diagonal() - 0.5 * off.sum(axis=1)
    J = 0.5 * np.triu(off, 1)
    return float(c), h, J


def basis_energies(Q: np.ndarray, chunk: int = 1 << 16) -> np.ndarray:
    """x'Qx for every computational basis state, Qiskit little-endian (bit i = qubit i)."""
    n = len(Q)
    out = np.empty(1 << n, float)
    bits = np.arange(n)
    for start in range(0, 1 << n, chunk):
        idx = np.arange(start, min(start + chunk, 1 << n), dtype=np.int64)
        X = ((idx[:, None] >> bits) & 1).astype(float)
        out[start:start + len(idx)] = np.einsum('si,ij,sj->s', X, Q, X, optimize=True)
    return out


def hamming_weights(n: int) -> np.ndarray:
    w = np.zeros(1 << n, np.int8)
    for bit in range(n):
        w += ((np.arange(1 << n, dtype=np.int64) >> bit) & 1).astype(np.int8)
    return w


def dicke_state(qc: QuantumCircuit, n: int, k: int) -> None:
    """Deterministic |D(n,k)> preparation (Baertschi & Eidenbenz, FCT 2019), O(nk) gates.

    Paper qubit p (1..n) is circuit qubit p-1. Start from |0^{n-k} 1^k>, then apply the
    split-and-cyclic-shift blocks SCS_{m,min(k,m-1)} for m = n .. 2.
    """
    if not 0 < k < n:
        raise ValueError('Dicke state needs 0 < k < n')
    q = lambda p: p - 1
    for p in range(n - k + 1, n + 1):
        qc.x(q(p))
    for m in range(n, 1, -1):
        l = min(k, m - 1)
        # gate (i) on paper qubits m-1, m
        qc.cx(q(m - 1), q(m))
        qc.cry(2 * np.arccos(np.sqrt(1 / m)), q(m), q(m - 1))
        qc.cx(q(m - 1), q(m))
        # gates (ii)_j on paper qubits m-j, m-j+1, m
        for j in range(2, l + 1):
            qc.cx(q(m - j), q(m))
            qc.append(RYGate(2 * np.arccos(np.sqrt(j / m))).control(2, annotated=False),
                      [q(m), q(m - j + 1), q(m - j)])
            qc.cx(q(m - j), q(m))


def qaoa_circuit(Q_cost: np.ndarray, k: int, reps: int, mixer: str) -> tuple[QuantumCircuit, ParameterVector, ParameterVector, float, float]:
    """Parameterised QAOA circuit for cost x'Q_cost x. Returns (circuit, betas, gammas, offset, scale).

    The cost unitary is exp(-i gamma (H - c)/scale) with H the exact Ising form of Q_cost.
    """
    n = len(Q_cost)
    c, h, J = ising_from_qubo(Q_cost)
    scale = float(np.sqrt((h ** 2).sum() + (J ** 2).sum()))  # std of H over the uniform superposition
    scale = max(scale, 1e-12)
    betas, gammas = ParameterVector('beta', reps), ParameterVector('gamma', reps)
    qc = QuantumCircuit(n)
    if mixer == 'x':
        qc.h(range(n))
    elif mixer == 'xy':
        dicke_state(qc, n, k)
    else:
        raise ValueError('mixer must be "x" or "xy"')
    ring = [(j, (j + 1) % n) for j in range(n)] if n > 2 else [(0, 1)]
    for layer in range(reps):
        for i in range(n):
            if h[i] != 0:
                qc.rz(2 * gammas[layer] * h[i] / scale, i)
        for i, j in zip(*np.nonzero(J)):
            qc.rzz(2 * gammas[layer] * J[i, j] / scale, int(i), int(j))
        if mixer == 'x':
            qc.rx(2 * betas[layer], range(n))
        else:
            for i, j in ring:  # exp(-i beta (XX+YY)/2) on each ring edge, sequential (Trotterised)
                qc.append(XXPlusYYGate(2 * betas[layer]), [i, j])
    return qc, betas, gammas, c, scale


def run_qaoa(Q: np.ndarray, k: int, *, reps: int, maxiter: int, shots: int, seed: int,
             mixer: str) -> tuple[np.ndarray, dict]:
    """Optimise QAOA angles with COBYLA on the exact simulated expectation, then sample and decode.

    Returns (selected indices, diagnostics). Diagnostics separate circuit
    construction + transpilation ('init_seconds'), the angle optimisation loop
    ('optimise_seconds') and sampling + decoding ('decode_seconds').
    """
    n = len(Q)
    if n > MAX_QAOA_QUBITS:
        raise ValueError(f'Statevector QAOA refused above {MAX_QAOA_QUBITS} qubits (2^n amplitudes)')
    tick = perf_counter()
    rng = np.random.default_rng(seed)
    Q = np.asarray(Q, float)
    penalty = cardinality_penalty(Q) if mixer == 'x' else 0.0
    Q_cost = penalised_qubo(Q, k, penalty) if mixer == 'x' else Q
    qc, betas, gammas, offset, scale = qaoa_circuit(Q_cost, k, reps, mixer)
    qc.save_probabilities()
    sim = AerSimulator(method='statevector', max_parallel_threads=1, seed_simulator=seed)
    compiled = transpile(qc, sim, optimization_level=1, seed_transpiler=seed)
    true_energy = basis_energies(Q)
    feasible = hamming_weights(n) == k
    levels = (basis_energies(Q_cost) - offset) / scale
    order = list(betas) + list(gammas)
    init_seconds = perf_counter() - tick
    evals = 0

    def probabilities(params: np.ndarray) -> np.ndarray:
        bound = compiled.assign_parameters(dict(zip(order, params)))
        p = np.asarray(sim.run(bound).result().data(0)['probabilities'], float)
        return p / p.sum()

    def loss(params: np.ndarray) -> float:
        nonlocal evals
        evals += 1
        return float(probabilities(params) @ levels)

    tick = perf_counter()
    fit = minimize(loss, rng.uniform(0, np.pi, 2 * reps), method='COBYLA',
                   options={'maxiter': maxiter, 'rhobeg': 0.8})
    optimise_seconds = perf_counter() - tick
    tick = perf_counter()
    p = probabilities(fit.x)
    samples = rng.choice(len(p), size=shots, p=p)
    valid = samples[feasible[samples]]
    feasible_mass = float(p[feasible].sum())
    if mixer == 'xy' and not np.isclose(feasible_mass, 1, atol=1e-7):
        raise AssertionError('XY mixer leaked amplitude out of the k-hot subspace')
    if len(valid) == 0:
        raise RuntimeError('QAOA sampled no feasible k-hot bitstring')
    best = int(valid[np.argmin(true_energy[valid])])
    selected = np.flatnonzero((best >> np.arange(n)) & 1)
    decode_seconds = perf_counter() - tick
    # Diagnostics only (never used for decoding). Judge the CIRCUIT, not shot luck: the exact
    # probability of an optimal k-hot string and the approximation ratio of the feasible-conditioned
    # output, each against a uniform sampler over the same start space with the SAME shot budget
    # (all 2^n strings for the X mixer, the C(n,k) k-hot strings for the XY mixer).
    e_star, e_worst = true_energy[feasible].min(), true_energy[feasible].max()
    optimal = feasible & np.isclose(true_energy, e_star, rtol=0, atol=1e-12 + 1e-9 * abs(e_star))
    start_space = (1 << n) if mixer == 'x' else comb(n, k)
    p_opt, p_uni = float(p[optimal].sum()), float(optimal.sum() / start_space)
    span = max(e_worst - e_star, 1e-300)
    pf = p[feasible] / max(p[feasible].sum(), 1e-300)
    approx = float((e_worst - pf @ true_energy[feasible]) / span)
    approx_uniform = float((e_worst - true_energy[feasible].mean()) / span)
    return selected, {
        'mixer': 'x_penalty' if mixer == 'x' else 'xy_ring_dicke',
        'qaoa_penalty': penalty,
        'qaoa_feasible_mass': feasible_mass,
        'qaoa_feasible_shots': int(len(valid)),
        'qaoa_evaluations': evals,
        'qaoa_success': bool(fit.success),
        'qaoa_optimal_mass': p_opt,
        'uniform_optimal_mass': p_uni,
        'qaoa_p_hit_in_shots': float(1 - (1 - p_opt) ** shots),
        'uniform_p_hit_in_shots': float(1 - (1 - p_uni) ** shots),
        'qaoa_approx_ratio': approx,
        'uniform_approx_ratio': approx_uniform,
        'qaoa_params': ';'.join(f'{v:.17g}' for v in fit.x),  # betas then gammas: reproduce the final state
        'qaoa_qubits': n,
        'qaoa_depth': int(compiled.depth()),
        'qaoa_multiqubit_gates': int(sum(1 for inst in qc.data
                                         if inst.operation.num_qubits >= 2 and inst.operation.name != 'save_probabilities')),
        'init_seconds': init_seconds,
        'optimise_seconds': optimise_seconds,
        'decode_seconds': decode_seconds,
        'simulator': 'qiskit-aer statevector (ideal, CPU) - NOT quantum hardware',
    }
