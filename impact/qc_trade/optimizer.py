"""Quadratic binary selection + bounded continuous portfolio refinement.

QAOA here is an IDEAL NUMPY STATEVECTOR simulator, not IBM hardware.
All methods must use the SAME objective and input for a fair benchmark.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from math import comb
from time import perf_counter
import numpy as np
from scipy.optimize import minimize, milp, Bounds, LinearConstraint
from scipy.sparse import lil_matrix


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


def exact_qubo(Q: np.ndarray, k: int, max_cases: int = 200_000) -> np.ndarray:
    if comb(len(Q), k) > max_cases:
        raise ValueError('Combinatorial search too large for exact QUBO solver')
    best = min(combinations(range(len(Q)), k), key=lambda ij: Q[np.ix_(ij, ij)].sum())
    return np.asarray(best, int)


def milp_qubo(Q: np.ndarray, k: int, time_limit: float=30.0) -> tuple[np.ndarray, dict]:
    """STRONG classical HiGHS MILP reference for same k-hot QUBO.

    McCormick linearization of z_ij=y_i*y_j with binary y and continuous z;
    globally optimal if HiGHS terminates with certified zero MIP gap.
    """
    n=len(Q)
    pairs=list(combinations(range(n),2))
    m=len(pairs)
    c=np.r_[Q.diagonal(), np.array([2*Q[i,j] for i,j in pairs])]
    a=lil_matrix((1+3*m,n+m),dtype=float)
    a[0,:n]=1
    lo=np.full(1+3*m,-np.inf)
    hi=np.full(1+3*m,np.inf)
    lo[0]=hi[0]=k
    for idx,(i,j) in enumerate(pairs):
        z=n+idx
        a[1+idx,i]=-1; a[1+idx,z]=1; hi[1+idx]=0
        a[1+m+idx,j]=-1; a[1+m+idx,z]=1; hi[1+m+idx]=0
        a[1+2*m+idx,i]=1; a[1+2*m+idx,j]=1; a[1+2*m+idx,z]=-1
        hi[1+2*m+idx]=1
    integrality=np.r_[np.ones(n,dtype=int),np.zeros(m,dtype=int)]
    fit=milp(c, integrality=integrality, bounds=Bounds(np.zeros(n+m),np.ones(n+m)),
             constraints=LinearConstraint(a.tocsr(),lo,hi),
             options={'time_limit':time_limit,'mip_rel_gap':1e-9})
    if fit.x is None:
        raise RuntimeError('HiGHS MILP found no feasible portfolio: '+str(fit.message))
    selected=np.flatnonzero(fit.x[:n] > .5)
    if len(selected)!=k:
        raise RuntimeError('HiGHS MILP returned invalid cardinality')
    return selected,{'milp_gap':float(fit.mip_gap) if fit.mip_gap is not None else np.nan,
                     'milp_nodes':int(fit.mip_node_count) if fit.mip_node_count is not None else -1,
                     'milp_certified':bool(fit.success and fit.mip_gap <= 1e-8)}


def greedy_swap(Q: np.ndarray, k: int) -> np.ndarray:
    """Classical local-search baseline; swap to best improving neighbor."""
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
    return np.asarray(indices, int)


def anneal_qubo(Q: np.ndarray, k: int, steps: int, restarts: int, seed: int) -> np.ndarray:
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


def qaoa_statevector(Q: np.ndarray, k: int, cfg: OptConfig, seed: int) -> tuple[np.ndarray, dict]:
    """Noiseless X-mixer QAOA, shot sampling, all costs/evaluations observable.

    No quantum hardware, no quantum runtime claim. The X mixer does not
    preserve cardinality; penalties plus feasible-sample filtering used.
    """
    n = len(Q)
    if n > 9:
        raise ValueError('Statevector QAOA demonstration is limited to <=9 binary variables')
    rng = np.random.default_rng(seed)
    penalty = max(4 * float(np.abs(Q).sum()), 1e-4)
    Qp = Q + penalty * np.ones_like(Q)
    Qp[np.diag_indices(n)] -= 2 * k * penalty
    states = np.arange(1 << n, dtype=np.int64)
    binary = ((states[:, None] >> np.arange(n)) & 1).astype(float)
    energies = np.einsum('si,ij,sj->s', binary, Qp, binary, optimize=True)
    energies = (energies - energies.mean()) / max(energies.std(), 1e-12)
    feasible = binary.sum(axis=1) == k
    pairs = [(states[(states >> bit & 1) == 0], states[(states >> bit & 1) == 0] + (1 << bit))
             for bit in range(n)]
    evals = 0

    def probs(params: np.ndarray) -> np.ndarray:
        amplitudes = np.full(1 << n, (1 / (1 << n))**.5, complex)
        for layer in range(cfg.qaoa_reps):
            amplitudes *= np.exp(-1j * params[cfg.qaoa_reps+layer] * energies)
            ca, sa = np.cos(params[layer]), np.sin(params[layer])
            for a, b in pairs:
                aa, bb = amplitudes[a].copy(), amplitudes[b].copy()
                amplitudes[a] = ca*aa - 1j*sa*bb
                amplitudes[b] = ca*bb - 1j*sa*aa
        return np.abs(amplitudes)**2

    def loss(params: np.ndarray) -> float:
        nonlocal evals
        evals += 1
        return float(probs(params) @ energies)

    fit = minimize(loss, rng.uniform(0, np.pi, 2*cfg.qaoa_reps), method='COBYLA',
                   options={'maxiter': cfg.qaoa_maxiter, 'rhobeg': 0.8})
    pp = probs(fit.x)
    samples = rng.choice(len(states), size=cfg.qaoa_shots, p=pp/pp.sum())
    valid = samples[feasible[samples]]
    if len(valid) == 0:
        raise RuntimeError('QAOA sampled no valid k-hot bitstrings')
    chosen = binary[valid[np.argmin(energies[valid])]].astype(int)
    return np.flatnonzero(chosen), {'qaoa_feasible_mass': float(pp[feasible].sum()),
                                     'qaoa_feasible_shots': int(len(valid)),
                                     'qaoa_evaluations': evals,
                                     'qaoa_success': bool(fit.success)}


def qaoa_xy_statevector(Q: np.ndarray, k: int, cfg: OptConfig, seed: int) -> tuple[np.ndarray, dict]:
    """Ideal QAOA with cardinality-PRESERVING partial-XY ring mixer.

    Initial |D(n,k)> = uniform computational basis superposition over k-hot
    states; XY mixers swap adjacent 01 and 10 states and preserve Hamming weight.
    The mixer acts as a sequential ring of 2-qubit gates (Trotterized). No
    quantum hardware/noise/calibration/transpilation simulated.
    """
    n=len(Q)
    if n>9:
        raise ValueError('Statevector QAOA XY capped at <=9 assets')
    rng=np.random.default_rng(seed)
    states=np.arange(1<<n,dtype=np.int64)
    binary=((states[:,None]>>np.arange(n)) & 1).astype(float)
    feasible=binary.sum(axis=1)==k
    energy=np.einsum('si,ij,sj->s',binary,Q,binary,optimize=True)
    levels=(energy-energy[feasible].mean())/max(energy[feasible].std(),1e-12)
    nstates=len(states)
    edges=[(j,(j+1)%n) for j in range(n)]
    pairs=[]
    for i,j in edges:
        lower=states[(((states>>i)&1)==0) & (((states>>j)&1)==1)]
        upper=lower ^ (1<<i) ^ (1<<j)
        pairs.append((lower,upper))
    evals=0
    def probs(params):
        a=np.zeros(nstates,complex)
        a[feasible]=1/np.sqrt(int(feasible.sum()))
        for layer in range(cfg.qaoa_reps):
            a *= np.exp(-1j*params[cfg.qaoa_reps+layer]*levels)
            ca,sa=np.cos(params[layer]),np.sin(params[layer])
            for left,right in pairs:
                x,y=a[left].copy(),a[right].copy()
                a[left]=ca*x-1j*sa*y
                a[right]=ca*y-1j*sa*x
        return np.abs(a)**2
    def loss(params):
        nonlocal evals
        evals+=1
        return float(probs(params)@levels)
    fit=minimize(loss,rng.uniform(0,np.pi,2*cfg.qaoa_reps),method='COBYLA',
                 options={'maxiter':cfg.qaoa_maxiter,'rhobeg':.8})
    probabilities=probs(fit.x)
    feasible_mass=float(probabilities[feasible].sum())
    if not np.isclose(feasible_mass,1,atol=1e-7):
        raise AssertionError('XY mixer unexpectedly violated cardinality')
    shots=rng.choice(nstates,size=cfg.qaoa_shots,p=probabilities/probabilities.sum())
    best=shots[np.argmin(energy[shots])]
    return np.flatnonzero(binary[best]), {'qaoa_feasible_mass':feasible_mass,
        'qaoa_feasible_shots':cfg.qaoa_shots,'qaoa_evaluations':evals,
        'qaoa_success':bool(fit.success),'mixer':'cardinality_preserving_xy_ring'}


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


def full_exact(mu: np.ndarray, cov: np.ndarray, prev: np.ndarray, cfg: OptConfig, max_cases=100) -> np.ndarray:
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
    Q = qubo_matrix(mu, cov, prev, cfg)
    extras: dict = {}
    if method == 'exact_qubo':
        indices = exact_qubo(Q, cfg.k)
    elif method == 'milp_qubo':
        indices,extras = milp_qubo(Q,cfg.k)
    elif method == 'greedy':
        indices = greedy_swap(Q, cfg.k)
    elif method == 'anneal':
        indices = anneal_qubo(Q, cfg.k, cfg.anneal_steps, cfg.anneal_restarts, seed)
    elif method == 'qaoa':
        indices, extras = qaoa_statevector(Q, cfg.k, cfg, seed)
    elif method == 'qaoa_xy':
        indices, extras = qaoa_xy_statevector(Q, cfg.k, cfg, seed)
    else:
        raise ValueError('Unrecognized method: '+method)
    w = refine(indices, mu, cov, prev, cfg)
    return w, {**extras, 'qubo_energy':qubo_energy(Q, indices),
               'runtime_seconds':perf_counter()-tick,
               'support':';'.join(str(i) for i in indices)}
