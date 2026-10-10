"""The QUBO and the classical solvers, vendored from QC-TRADE.

Vendored (a justified fork: a Qollab project must be a self-contained folder that runs in Pyodide) from
`impact/qc_trade/optimizer.py` at commit 89006f4 of https://github.com/udsy19/Qollab-Hackathon. The maths
is unchanged. Changes: `scipy.optimize.milp` is imported lazily so its absence is reported, not fatal;
the NumPy QAOA simulators are NOT vendored (the Qiskit circuits in `qaoa.py` replace them); the trading
and backtest parts are left out.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import comb

import numpy as np
from scipy.optimize import minimize


@dataclass(frozen=True)
class OptConfig:
    k: int = 2
    risk_aversion: float = 6.0
    min_weight: float = 0.03
    max_weight: float = 0.80
    expected_cost_bps: float = 4.0  # prior for the optimiser; not an executable fill cost
    anneal_steps: int = 300
    anneal_restarts: int = 4


def validate_config(cfg: OptConfig, n: int) -> None:
    if not 1 <= cfg.k < n:
        raise ValueError('Use 1 <= k < number of tickers (cash is implicit)')
    if not cfg.k * cfg.min_weight <= 1 <= cfg.k * cfg.max_weight:
        raise ValueError('Infeasible k and portfolio weight limits')
    if cfg.expected_cost_bps < 0 or cfg.risk_aversion < 0:
        raise ValueError('Risk and trading cost parameters must not be negative')


def qubo_matrix(mu: np.ndarray, cov: np.ndarray, prev: np.ndarray, cfg: OptConfig) -> np.ndarray:
    """Exact equal-weight k-support QUBO, with linear turnover cost.

    E(y) = -mu'y/k + .5 gamma/k^2 y' Cov y + c||y/k-prev||_1   (constant c sum(prev) omitted).
    Feasibility sum(y)=k is enforced by the k-swap and enumeration solvers, by the MILP's equality row,
    by a cardinality penalty for X-mixer QAOA, and by the Hamming-weight-preserving XY mixer.
    """
    n = len(mu)
    validate_config(cfg, n)
    prev = np.asarray(prev, float)
    Q = .5 * cfg.risk_aversion * np.asarray(cov, float) / (cfg.k * cfg.k)
    Q = Q.copy()
    c = cfg.expected_cost_bps * 1e-4
    Q[np.diag_indices(n)] += -mu / cfg.k + c * (np.abs(1/cfg.k - prev) - np.abs(prev))
    return (Q + Q.T) / 2


def qubo_energy(Q: np.ndarray, indices) -> float:
    x = np.zeros(len(Q), float)
    x[np.asarray(indices, int)] = 1
    return float(x @ Q @ x)


def exact_qubo(Q: np.ndarray, k: int, max_cases: int = 200_000) -> np.ndarray:
    if comb(len(Q), k) > max_cases:
        raise ValueError('Combinatorial search too large for exact QUBO solver')
    best = min(combinations(range(len(Q)), k), key=lambda ij: Q[np.ix_(ij, ij)].sum())
    return np.asarray(best, int)


def milp_qubo(Q: np.ndarray, k: int, time_limit: float = 30.0) -> tuple[np.ndarray, dict]:
    """Strong classical HiGHS MILP reference for the same k-hot QUBO.

    McCormick linearisation of z_ij = y_i*y_j with binary y and continuous z; globally optimal if HiGHS
    terminates with a certified zero MIP gap. Raises ImportError where scipy has no `milp` (HiGHS).
    """
    from scipy.optimize import milp, Bounds, LinearConstraint  # lazy: may be absent in a Pyodide build
    from scipy.sparse import lil_matrix
    n = len(Q)
    pairs = list(combinations(range(n), 2))
    m = len(pairs)
    c = np.r_[Q.diagonal(), np.array([2*Q[i, j] for i, j in pairs])]
    a = lil_matrix((1+3*m, n+m), dtype=float)
    a[0, :n] = 1
    lo = np.full(1+3*m, -np.inf)
    hi = np.full(1+3*m, np.inf)
    lo[0] = hi[0] = k
    for idx, (i, j) in enumerate(pairs):
        z = n+idx
        a[1+idx, i] = -1; a[1+idx, z] = 1; hi[1+idx] = 0
        a[1+m+idx, j] = -1; a[1+m+idx, z] = 1; hi[1+m+idx] = 0
        a[1+2*m+idx, i] = 1; a[1+2*m+idx, j] = 1; a[1+2*m+idx, z] = -1
        hi[1+2*m+idx] = 1
    integrality = np.r_[np.ones(n, dtype=int), np.zeros(m, dtype=int)]
    fit = milp(c, integrality=integrality, bounds=Bounds(np.zeros(n+m), np.ones(n+m)),
               constraints=LinearConstraint(a.tocsr(), lo, hi),
               options={'time_limit': time_limit, 'mip_rel_gap': 1e-9})
    if fit.x is None:
        raise RuntimeError('HiGHS MILP found no feasible portfolio: '+str(fit.message))
    selected = np.flatnonzero(fit.x[:n] > .5)
    if len(selected) != k:
        raise RuntimeError('HiGHS MILP returned invalid cardinality')
    gap = getattr(fit, 'mip_gap', None)
    return selected, {'milp_gap': float(gap) if gap is not None else float('nan'),
                      'milp_certified': bool(fit.success and gap is not None and gap <= 1e-8)}


def greedy_swap(Q: np.ndarray, k: int) -> np.ndarray:
    """Classical local-search baseline: start from the k best diagonal terms, swap to the best improving neighbour."""
    n = len(Q)
    indices = np.argsort(Q.diagonal())[:k]
    best_value = qubo_energy(Q, indices)
    for _ in range(100):
        changed = False
        for i in indices:
            for j in range(n):
                if j in indices:
                    continue
                new_idx = np.array(sorted((set(indices) - {int(i)}) | {j}), dtype=int)
                val = qubo_energy(Q, new_idx)
                if val < best_value - 1e-12:
                    best_value = val
                    best_next = new_idx
                    changed = True
        if not changed:
            break
        indices = best_next
    return np.sort(np.asarray(indices, int))


def anneal_qubo(Q: np.ndarray, k: int, steps: int, restarts: int, seed: int) -> np.ndarray:
    """Simulated annealing over k-hot states with swap moves (restart 0 starts from greedy)."""
    rng = np.random.default_rng(seed)
    n = len(Q)
    if not 0 < k < n:
        raise ValueError('k must be within asset universe')
    temp0 = max(float(np.std(Q)) * k, 1e-7)
    best, best_value = None, np.inf
    for restart in range(restarts):
        indices = (greedy_swap(Q, k) if restart == 0 else rng.choice(n, size=k, replace=False))
        x = np.zeros(n, float)
        x[indices] = 1
        val = qubo_energy(Q, indices)
        if val < best_value:
            best, best_value = indices.copy(), val
        for step in range(steps):
            i = int(rng.choice(np.flatnonzero(x > .5)))
            j = int(rng.choice(np.flatnonzero(x < .5)))
            d = np.zeros(n)
            d[i], d[j] = -1, 1
            delta = float(2 * d @ Q @ x + d @ Q @ d)
            temp = temp0 * (.001 ** (step / max(steps-1, 1)))
            if delta <= 0 or rng.random() < np.exp(-min(700, max(0, delta)/temp)):
                x[i], x[j] = 0, 1
                val += delta
                if val < best_value - 1e-12:
                    best_value, best = val, np.flatnonzero(x).copy()
    return np.sort(best)


def portfolio_objective(w: np.ndarray, mu: np.ndarray, cov: np.ndarray, prev: np.ndarray, cfg: OptConfig) -> float:
    return float(.5*cfg.risk_aversion*w@cov@w - mu@w + cfg.expected_cost_bps*1e-4 * np.abs(w-prev).sum())


def refine(indices: np.ndarray, mu: np.ndarray, cov: np.ndarray, prev: np.ndarray, cfg: OptConfig) -> np.ndarray:
    """Stage B: convex, bounded, fully invested continuous sizing on the selected support (SLSQP)."""
    indices = np.sort(np.asarray(indices, dtype=int))
    n = len(mu)
    if len(indices) != cfg.k or len(set(indices.tolist())) != cfg.k:
        raise ValueError('Selected support must have exactly k distinct assets')
    validate_config(cfg, n)
    cc = cov[np.ix_(indices, indices)]
    m = mu[indices]
    old = prev[indices]
    c = cfg.expected_cost_bps*1e-4
    eps = 1e-9  # smooths |.| for SLSQP only; the reported objective uses the true L1 norm

    def loss(x):
        d = x-old
        return float(.5*cfg.risk_aversion*x@cc@x - m@x + c*np.sqrt(d*d+eps*eps).sum())

    def jac(x):
        d = x-old
        return cfg.risk_aversion*(cc@x)-m+c*d/np.sqrt(d*d+eps*eps)
    fit = minimize(loss, np.repeat(1/cfg.k, cfg.k), method='SLSQP', jac=jac,
                   bounds=[(cfg.min_weight, cfg.max_weight)]*cfg.k,
                   constraints=[{'type': 'eq', 'fun': lambda x: float(x.sum()-1),
                                 'jac': lambda x: np.ones_like(x)}],
                   options={'maxiter': 220, 'ftol': 1e-12})
    if abs(fit.x.sum()-1) > 1e-5 or (fit.x < cfg.min_weight-1e-5).any() or (fit.x > cfg.max_weight+1e-5).any():
        raise RuntimeError('Continuous refinement failed feasibility: '+str(fit.message))
    w = np.zeros(n)
    w[indices] = fit.x
    return w
