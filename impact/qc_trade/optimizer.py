"""Two-stage hybrid: (A) k-hot asset selection as a QUBO, (B) bounded continuous refinement.

Stage A solvers all minimise the SAME energy x'Qx (``qubo_matrix``) over the
SAME feasible set {x binary, sum x = k}:

* exact_qubo   exhaustive enumeration (certified optimum, small C(n,k) only)
* milp_qubo    HiGHS MILP, McCormick + RLT linearisation (certified when gap 0)
* greedy       best-improvement swap local search (k-hot throughout)
* anneal       simulated annealing over k-hot swaps (k-hot throughout)
* random_khot  uniform random k-subsets, best of `qaoa_shots` (the QAOA control)
* qaoa         X-mixer QAOA on x'Qx + P(sum x - k)^2; P provably keeps the
               penalised optimum k-hot and equal to the constrained optimum;
               infeasible samples discarded at decoding (formulation differs:
               penalty, not hard constraint - see qaoa.cardinality_penalty)
* qaoa_xy      XY-mixer QAOA, Dicke start, never leaves the k-hot subspace

QAOA here is an IDEAL statevector simulation (Qiskit circuits, qiskit-aer on
the CPU). It is not quantum hardware and its runtime is not a quantum runtime.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations, islice
from math import comb
from time import perf_counter
import numpy as np
from scipy.optimize import minimize, milp, Bounds, LinearConstraint
from scipy.sparse import lil_matrix
from .qaoa import run_qaoa


@dataclass(frozen=True)
class OptConfig:
    k: int = 2
    risk_aversion: float = 6.0
    min_weight: float = 0.03
    max_weight: float = 0.80
    expected_cost_bps: float = 4.0  # prior for optimizer; not the executable fill cost
    anneal_steps: int = 300
    anneal_restarts: int = 4
    qaoa_reps: int = 2
    qaoa_maxiter: int = 80
    qaoa_shots: int = 1024
    milp_time_limit: float = 30.0
    seed: int = 37


def validate_config(cfg: OptConfig, n: int) -> None:
    if not 1 <= cfg.k < n:
        raise ValueError('Use 1 <= k < number of tickers (cash is implicit)')
    if not cfg.k * cfg.min_weight <= 1 <= cfg.k * cfg.max_weight:
        raise ValueError('Infeasible k and portfolio weight limits')
    if cfg.expected_cost_bps < 0 or cfg.risk_aversion < 0:
        raise ValueError('Risk and trading cost parameters must not be negative')


def qubo_matrix(mu: np.ndarray, cov: np.ndarray, prev: np.ndarray, cfg: OptConfig) -> np.ndarray:
    """Exact equal-weight k-support QUBO, with linear turnover cost.

    E(y) = -mu'y/k + .5 gamma/k² y' Cov y + c||y/k-prev||_1.
    Constant c sum(prev) omitted. Feasibility sum(y)=k is enforced by k-swap
    and enumeration solvers, and by a cardinality penalty for X-mixer QAOA.
    """
    n = len(mu)
    validate_config(cfg, n)
    prev = np.asarray(prev, float)
    Q = .5 * cfg.risk_aversion * np.asarray(cov, float) / (cfg.k * cfg.k)
    Q = Q.copy()
    c = cfg.expected_cost_bps * 1e-4
    Q[np.diag_indices(n)] += -mu / cfg.k + c * (np.abs(1/cfg.k - prev) - np.abs(prev))
    return (Q + Q.T) / 2


def qubo_energy(Q: np.ndarray, indices: np.ndarray) -> float:
    x = np.zeros(len(Q), float)
    x[np.asarray(indices, int)] = 1
    return float(x @ Q @ x)


def exact_qubo(Q: np.ndarray, k: int, max_cases: int = 1_000_000, chunk: int = 50_000) -> np.ndarray:
    """Exhaustive search over all C(n,k) supports, vectorised in chunks. Ties: lowest lexicographic."""
    n = len(Q)
    if comb(n, k) > max_cases:
        raise ValueError(f'Combinatorial search too large for exact QUBO solver: C({n},{k})={comb(n, k)}')
    Q = np.asarray(Q, float)
    supports = combinations(range(n), k)
    best, best_value = None, np.inf
    while True:
        block = np.array(list(islice(supports, chunk)), dtype=np.int64)
        if not len(block):
            break
        values = Q[block[:, :, None], block[:, None, :]].sum(axis=(1, 2))
        i = int(np.argmin(values))
        if values[i] < best_value - 1e-15:
            best, best_value = block[i], float(values[i])
    return np.asarray(best, int)


def milp_qubo(Q: np.ndarray, k: int, time_limit: float = 30.0, rlt: bool = True) -> tuple[np.ndarray, dict]:
    """STRONG classical HiGHS MILP for the same k-hot QUBO (scipy.optimize.milp).

    McCormick linearisation z_ij = y_i y_j (z <= y_i, z <= y_j, z >= y_i + y_j - 1)
    with binary y. ``rlt=True`` adds the reformulation-linearisation cuts
    sum_{j != i} z_ij = (k-1) y_i, valid because sum_j y_j = k; they tighten the
    LP relaxation without changing the integer feasible set. Globally optimal
    if HiGHS terminates with a certified zero MIP gap ('milp_certified').
    """
    n = len(Q)
    pairs = list(combinations(range(n), 2))
    m = len(pairs)
    c = np.r_[Q.diagonal(), np.array([2 * Q[i, j] for i, j in pairs])]
    rows = 1 + 3 * m + (n if rlt else 0)
    a = lil_matrix((rows, n + m), dtype=float)
    a[0, :n] = 1
    lo = np.full(rows, -np.inf)
    hi = np.full(rows, np.inf)
    lo[0] = hi[0] = k
    for idx, (i, j) in enumerate(pairs):
        z = n + idx
        a[1 + idx, i] = -1; a[1 + idx, z] = 1; hi[1 + idx] = 0
        a[1 + m + idx, j] = -1; a[1 + m + idx, z] = 1; hi[1 + m + idx] = 0
        a[1 + 2 * m + idx, i] = 1; a[1 + 2 * m + idx, j] = 1; a[1 + 2 * m + idx, z] = -1
        hi[1 + 2 * m + idx] = 1
        if rlt:
            for v in (i, j):
                a[1 + 3 * m + v, z] = 1
    if rlt:
        for v in range(n):
            a[1 + 3 * m + v, v] = -(k - 1)
            lo[1 + 3 * m + v] = hi[1 + 3 * m + v] = 0
    integrality = np.r_[np.ones(n, dtype=int), np.zeros(m, dtype=int)]
    fit = milp(c, integrality=integrality, bounds=Bounds(np.zeros(n + m), np.ones(n + m)),
               constraints=LinearConstraint(a.tocsr(), lo, hi),
               options={'time_limit': time_limit, 'mip_rel_gap': 1e-9})
    if fit.x is None:
        raise RuntimeError('HiGHS MILP found no feasible portfolio: ' + str(fit.message))
    selected = np.flatnonzero(fit.x[:n] > .5)
    if len(selected) != k:
        raise RuntimeError('HiGHS MILP returned invalid cardinality')
    gap = float(fit.mip_gap) if fit.mip_gap is not None else np.nan
    return selected, {'milp_gap': gap,
                      'milp_nodes': int(fit.mip_node_count) if fit.mip_node_count is not None else -1,
                      'milp_certified': bool(fit.success and gap <= 1e-8),
                      'milp_status': str(fit.message)[:80]}


def _swap_deltas(Q: np.ndarray, Qx: np.ndarray, ones: np.ndarray, zeros: np.ndarray) -> np.ndarray:
    """Energy change of every swap (i in ones -> out, j in zeros -> in): rows i, columns j."""
    d = Q.diagonal()
    return (2 * (Qx[zeros][None, :] - Qx[ones][:, None]) + d[ones][:, None] + d[zeros][None, :]
            - 2 * Q[np.ix_(ones, zeros)])


def greedy_swap(Q: np.ndarray, k: int) -> np.ndarray:
    """Classical local search: start from the k best diagonal terms, take the best improving swap until none."""
    n = len(Q)
    x = np.zeros(n, bool)
    x[np.argsort(Q.diagonal(), kind='stable')[:k]] = True
    Qx = Q[:, x].sum(axis=1)
    for _ in range(10 * n):
        ones, zeros = np.flatnonzero(x), np.flatnonzero(~x)
        deltas = _swap_deltas(Q, Qx, ones, zeros)
        r, c = np.unravel_index(int(np.argmin(deltas)), deltas.shape)
        if deltas[r, c] >= -1e-15:
            break
        i, j = ones[r], zeros[c]
        x[i], x[j] = False, True
        Qx += Q[:, j] - Q[:, i]
    return np.flatnonzero(x)


def anneal_qubo(Q: np.ndarray, k: int, steps: int, restarts: int, seed: int) -> np.ndarray:
    """Simulated annealing over k-hot swaps (cardinality is never violated), O(n) per accepted move.

    Restart 0 starts from the greedy solution, later restarts from random supports.
    Geometric cooling from temp0 = k std(Q) to 1e-3 temp0.
    """
    rng = np.random.default_rng(seed)
    n = len(Q)
    if not 0 < k < n:
        raise ValueError('k must be within asset universe')
    d = Q.diagonal()
    temp0 = max(float(np.std(Q)) * k, 1e-12)
    best, best_value = None, np.inf
    for restart in range(restarts):
        start = greedy_swap(Q, k) if restart == 0 else rng.choice(n, size=k, replace=False)
        x = np.zeros(n, bool)
        x[start] = True
        Qx = Q[:, x].sum(axis=1)
        val = float(Qx[x].sum())
        if val < best_value - 1e-15:
            best, best_value = np.flatnonzero(x), val
        for step in range(steps):
            i = int(rng.choice(np.flatnonzero(x)))
            j = int(rng.choice(np.flatnonzero(~x)))
            delta = float(2 * (Qx[j] - Qx[i]) + d[i] + d[j] - 2 * Q[i, j])
            temp = temp0 * (.001 ** (step / max(steps - 1, 1)))
            if delta <= 0 or rng.random() < np.exp(-min(700, delta / temp)):
                x[i], x[j] = False, True
                Qx += Q[:, j] - Q[:, i]
                val += delta
                if val < best_value - 1e-15:
                    best, best_value = np.flatnonzero(x), val
    return np.sort(best)


def random_khot(Q: np.ndarray, k: int, shots: int, seed: int) -> np.ndarray:
    """CONTROL for QAOA: draw `shots` uniform random k-subsets and keep the lowest x'Qx.

    Same sample budget and same decoding rule as QAOA's final sampling step, so a
    QAOA result that this does not beat shows no benefit from the circuit.
    """
    rng = np.random.default_rng(seed)
    n = len(Q)
    block = np.argsort(rng.random((shots, n)), axis=1)[:, :k]
    values = Q[block[:, :, None], block[:, None, :]].sum(axis=(1, 2))
    return np.sort(block[int(np.argmin(values))])


def qaoa_statevector(Q: np.ndarray, k: int, cfg: OptConfig, seed: int) -> tuple[np.ndarray, dict]:
    """Standard X-mixer QAOA with provable cardinality penalty, Qiskit circuit, ideal Aer simulation."""
    return run_qaoa(Q, k, reps=cfg.qaoa_reps, maxiter=cfg.qaoa_maxiter, shots=cfg.qaoa_shots,
                    seed=seed, mixer='x')


def qaoa_xy_statevector(Q: np.ndarray, k: int, cfg: OptConfig, seed: int) -> tuple[np.ndarray, dict]:
    """Cardinality-preserving XY-ring QAOA from a Dicke state, Qiskit circuit, ideal Aer simulation."""
    return run_qaoa(Q, k, reps=cfg.qaoa_reps, maxiter=cfg.qaoa_maxiter, shots=cfg.qaoa_shots,
                    seed=seed, mixer='xy')


def portfolio_objective(w: np.ndarray, mu: np.ndarray, cov: np.ndarray, prev: np.ndarray, cfg: OptConfig) -> float:
    return float(.5*cfg.risk_aversion*w@cov@w - mu@w + cfg.expected_cost_bps*1e-4 * np.abs(w-prev).sum())


def refine(indices: np.ndarray, mu: np.ndarray, cov: np.ndarray, prev: np.ndarray, cfg: OptConfig) -> np.ndarray:
    """Convex bounded full-investment continuous sizing on selected support."""
    indices = np.sort(np.asarray(indices, dtype=int))
    n = len(mu)
    if len(indices) != cfg.k or len(set(indices)) != cfg.k:
        raise ValueError('Selected support must have exactly k distinct assets')
    validate_config(cfg, n)
    cc = cov[np.ix_(indices, indices)]
    m = mu[indices]
    old = prev[indices]
    c = cfg.expected_cost_bps*1e-4
    # Smooth only for numerical SLSQP objective; reported objective is true L1.
    eps = 1e-9
    def loss(x):
        d = x-old
        return float(.5*cfg.risk_aversion*x@cc@x - m@x + c*np.sqrt(d*d+eps*eps).sum())
    def jac(x):
        d = x-old
        return cfg.risk_aversion*(cc@x)-m+c*d/np.sqrt(d*d+eps*eps)
    fit = minimize(loss, np.repeat(1/cfg.k, cfg.k), method='SLSQP', jac=jac,
                   bounds=[(cfg.min_weight, cfg.max_weight)]*cfg.k,
                   constraints=[{'type':'eq','fun':lambda x:float(x.sum()-1),
                                 'jac':lambda x:np.ones_like(x)}],
                   options={'maxiter':220, 'ftol':1e-12})
    if abs(fit.x.sum()-1)>1e-5 or (fit.x < cfg.min_weight-1e-5).any() or (fit.x>cfg.max_weight+1e-5).any():
        raise RuntimeError('Continuous refinement failed feasibility: '+str(fit.message))
    w = np.zeros(n)
    w[indices] = fit.x
    return w


def full_exact(mu: np.ndarray, cov: np.ndarray, prev: np.ndarray, cfg: OptConfig, max_cases=2000) -> np.ndarray:
    if comb(len(mu), cfg.k) > max_cases:
        raise ValueError('Too many supports for full continuous enumeration')
    best_w, best_obj = None, float('inf')
    for support in combinations(range(len(mu)), cfg.k):
        w = refine(np.array(support), mu, cov, prev, cfg)
        val = portfolio_objective(w, mu, cov, prev, cfg)
        if val < best_obj:
            best_w, best_obj = w, val
    return best_w


def choose(method: str, mu: np.ndarray, cov: np.ndarray, prev: np.ndarray,
           cfg: OptConfig, seed: int) -> tuple[np.ndarray, dict]:
    """Returns (weights, diagnostics) and reports all preprocessing+solver+refinement time."""
    tick = perf_counter()
    n = len(mu)
    validate_config(cfg, n)
    if method == 'cash':
        return np.zeros(n), {'runtime_seconds': perf_counter()-tick}
    if method == 'spy':
        weights = np.zeros(n)
        weights[0] = 1.0  # universe order required: SPY first
        return weights, {'runtime_seconds': perf_counter()-tick}
    if method == 'equal':
        return np.repeat(1/n, n), {'runtime_seconds': perf_counter()-tick}
    if method == 'topk':
        indices = np.argsort(mu)[-cfg.k:]
        return refine(indices, mu, cov, prev, cfg), {'runtime_seconds':perf_counter()-tick}
    if method == 'minvar':
        indices = np.argsort(np.diag(cov))[:cfg.k]
        return refine(indices, np.zeros(n), cov, prev, cfg), {'runtime_seconds':perf_counter()-tick}
    if method == 'full_exact':
        w = full_exact(mu, cov, prev, cfg)
        return w, {'runtime_seconds':perf_counter()-tick}
    construct = perf_counter()
    Q = qubo_matrix(mu, cov, prev, cfg)
    construct_seconds = perf_counter() - construct
    solve = perf_counter()
    extras: dict = {}
    if method == 'exact_qubo':
        indices = exact_qubo(Q, cfg.k)
    elif method == 'milp_qubo':
        indices, extras = milp_qubo(Q, cfg.k, time_limit=cfg.milp_time_limit)
    elif method == 'greedy':
        indices = greedy_swap(Q, cfg.k)
    elif method == 'anneal':
        indices = anneal_qubo(Q, cfg.k, cfg.anneal_steps, cfg.anneal_restarts, seed)
    elif method == 'random_khot':
        indices = random_khot(Q, cfg.k, cfg.qaoa_shots, seed)
    elif method == 'qaoa':
        indices, extras = qaoa_statevector(Q, cfg.k, cfg, seed)
    elif method == 'qaoa_xy':
        indices, extras = qaoa_xy_statevector(Q, cfg.k, cfg, seed)
    else:
        raise ValueError('Unrecognized method: '+method)
    solve_seconds = perf_counter() - solve
    polish = perf_counter()
    w = refine(indices, mu, cov, prev, cfg)
    refine_seconds = perf_counter() - polish
    return w, {**extras, 'qubo_energy': qubo_energy(Q, indices),
               'construct_seconds': construct_seconds, 'solve_seconds': solve_seconds,
               'refine_seconds': refine_seconds, 'runtime_seconds': perf_counter()-tick,
               'support': ';'.join(str(i) for i in indices)}
