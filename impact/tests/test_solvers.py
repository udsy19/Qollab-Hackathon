"""Solver gate: same objective, same constraints, feasibility, seed determinism, Qiskit-vs-NumPy QAOA.

The NumPy statevector below is an INDEPENDENT oracle (it never imports the
Qiskit path); the Qiskit circuits must reproduce it amplitude for amplitude.
"""
from itertools import combinations
from math import comb
import numpy as np
import pytest
from qiskit.quantum_info import Statevector
from qc_trade.optimizer import (OptConfig, qubo_matrix, qubo_energy, exact_qubo, milp_qubo,
                                greedy_swap, anneal_qubo, random_khot, choose, refine,
                                portfolio_objective)
from qc_trade.qaoa import (cardinality_penalty, penalised_qubo, ising_from_qubo, basis_energies,
                           dicke_state, qaoa_circuit, run_qaoa)
from qc_trade.scaling import make_instance, plan_runs


def _rand_qubo(n, seed):
    q = np.random.default_rng(seed).normal(size=(n, n))
    return (q + q.T) / 2


def _brute(Q, k):
    return min(qubo_energy(Q, np.array(s)) for s in combinations(range(len(Q)), k))


# ---------------------------------------------------------------- NumPy oracle
def _numpy_qaoa_probs(Q_cost, k, params, reps, mixer, offset, scale):
    n = len(Q_cost)
    states = np.arange(1 << n)
    binary = ((states[:, None] >> np.arange(n)) & 1).astype(float)
    levels = (np.einsum('si,ij,sj->s', binary, Q_cost, binary) - offset) / scale
    if mixer == 'x':
        a = np.full(1 << n, (1 / (1 << n)) ** .5, complex)
        pairs = [(states[(states >> b & 1) == 0], states[(states >> b & 1) == 0] + (1 << b)) for b in range(n)]
    else:
        feasible = binary.sum(1) == k
        a = np.zeros(1 << n, complex)
        a[feasible] = 1 / np.sqrt(feasible.sum())
        pairs = []
        for i, j in [(j, (j + 1) % n) for j in range(n)]:
            lower = states[(((states >> i) & 1) == 0) & (((states >> j) & 1) == 1)]
            pairs.append((lower, lower ^ (1 << i) ^ (1 << j)))
    for layer in range(reps):
        a = a * np.exp(-1j * params[reps + layer] * levels)
        ca, sa = np.cos(params[layer]), np.sin(params[layer])
        for left, right in pairs:
            x, y = a[left].copy(), a[right].copy()
            a[left] = ca * x - 1j * sa * y
            a[right] = ca * y - 1j * sa * x
    return np.abs(a) ** 2


# ---------------------------------------------------------------- formulation equivalence
def test_ising_mapping_exact_on_every_bitstring():
    Q = _rand_qubo(6, 1)
    c, h, J = ising_from_qubo(Q)
    E = basis_energies(Q)
    for s in range(1 << 6):
        z = 1 - 2 * ((s >> np.arange(6)) & 1)
        assert np.isclose(c + h @ z + z @ J @ z, E[s], atol=1e-12)


@pytest.mark.parametrize('seed', range(12))
def test_penalty_keeps_ground_state_k_hot_and_optimal(seed):
    n, k = 7, 3
    Q = _rand_qubo(n, 100 + seed)
    Qp = penalised_qubo(Q, k, cardinality_penalty(Q))
    E = basis_energies(Qp)
    weights = np.array([bin(s).count('1') for s in range(1 << n)])
    ground = E.min()
    assert np.all(weights[np.isclose(E, ground, atol=1e-9)] == k)
    assert np.isclose(ground + cardinality_penalty(Q) * k * k, _brute(Q, k), atol=1e-9)


def test_penalised_qubo_equals_qubo_plus_constant_on_feasible():
    Q = _rand_qubo(6, 4)
    P = cardinality_penalty(Q)
    Qp = penalised_qubo(Q, 2, P)
    for s in combinations(range(6), 2):
        assert np.isclose(qubo_energy(Qp, np.array(s)) + P * 4, qubo_energy(Q, np.array(s)))


@pytest.mark.parametrize('n,k', [(4, 2), (5, 2), (6, 3), (7, 1), (8, 5)])
def test_dicke_circuit_is_uniform_over_k_hot(n, k):
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(n)
    dicke_state(qc, n, k)
    p = Statevector(qc).probabilities()
    w = np.array([bin(s).count('1') for s in range(1 << n)])
    assert np.allclose(p[w == k], 1 / comb(n, k), atol=1e-10)
    assert np.allclose(p[w != k], 0, atol=1e-10)


@pytest.mark.parametrize('mixer', ['x', 'xy'])
def test_qiskit_qaoa_matches_numpy_oracle(mixer):
    n, k, reps = 5, 2, 2
    Q = _rand_qubo(n, 9)
    Q_cost = penalised_qubo(Q, k, cardinality_penalty(Q)) if mixer == 'x' else Q
    qc, betas, gammas, offset, scale = qaoa_circuit(Q_cost, k, reps, mixer)
    params = np.array([.31, .72, .45, 1.1])
    bound = qc.assign_parameters(dict(zip(list(betas) + list(gammas), params)))
    p_qiskit = Statevector(bound).probabilities()
    p_numpy = _numpy_qaoa_probs(Q_cost, k, params, reps, mixer, offset, scale)
    assert np.allclose(p_qiskit, p_numpy, atol=1e-10)


# ---------------------------------------------------------------- same objective across solvers
@pytest.mark.parametrize('n,k,seed', [(6, 2, 0), (8, 3, 1), (10, 4, 2), (12, 3, 3)])
def test_exact_and_both_milp_formulations_agree_with_brute_force(n, k, seed):
    Q = _rand_qubo(n, seed)
    ref = _brute(Q, k)
    assert np.isclose(qubo_energy(Q, exact_qubo(Q, k)), ref, atol=1e-9)
    for rlt in (True, False):
        sel, info = milp_qubo(Q, k, rlt=rlt)
        assert len(sel) == k and info['milp_certified']
        assert np.isclose(qubo_energy(Q, sel), ref, atol=1e-7)


def test_milp_certifies_at_scaling_size():
    inst = make_instance(30, 6, seed=5, regime='hard')
    Q = qubo_matrix(inst['mu'], inst['cov'], inst['prev'], inst['cfg'])
    sel, info = milp_qubo(Q, 6, time_limit=60)
    assert info['milp_certified']
    assert np.isclose(qubo_energy(Q, sel), qubo_energy(Q, exact_qubo(Q, 6, max_cases=1_000_000)), atol=1e-10)


@pytest.mark.parametrize('method', ['greedy', 'anneal', 'random_khot', 'qaoa', 'qaoa_xy', 'exact_qubo', 'milp_qubo'])
def test_every_qubo_solver_is_feasible_and_never_beats_exact(method):
    cfg = OptConfig(k=2, qaoa_maxiter=25, qaoa_shots=128, anneal_steps=60, anneal_restarts=2)
    inst = make_instance(6, 2, seed=11, regime='hard')
    mu, cov, prev = inst['mu'], inst['cov'], inst['prev']
    cfg = OptConfig(**{**inst['cfg'].__dict__, 'qaoa_maxiter': 25, 'qaoa_shots': 128,
                       'anneal_steps': 60, 'anneal_restarts': 2})
    Q = qubo_matrix(mu, cov, prev, cfg)
    w, d = choose(method, mu, cov, prev, cfg, seed=3)
    support = np.flatnonzero(w > 1e-9)
    assert len(support) == cfg.k and np.isclose(w.sum(), 1)
    assert np.isclose(d['qubo_energy'], qubo_energy(Q, support))
    assert d['qubo_energy'] >= _brute(Q, cfg.k) - 1e-12
    for key in ('construct_seconds', 'solve_seconds', 'refine_seconds', 'runtime_seconds'):
        assert d[key] >= 0


def test_refinement_never_worse_than_equal_weight_on_same_support():
    inst = make_instance(10, 3, seed=2, regime='trading')
    mu, cov, prev, cfg = inst['mu'], inst['cov'], inst['prev'], inst['cfg']
    for s in [(0, 1, 2), (3, 5, 9)]:
        w = refine(np.array(s), mu, cov, prev, cfg)
        eq = np.zeros(10); eq[list(s)] = 1 / 3
        assert portfolio_objective(w, mu, cov, prev, cfg) <= portfolio_objective(eq, mu, cov, prev, cfg) + 1e-12


# ---------------------------------------------------------------- QAOA feasibility
def test_xy_qaoa_never_leaves_k_hot_subspace():
    Q = _rand_qubo(7, 21)
    sel, d = run_qaoa(Q, 3, reps=2, maxiter=20, shots=200, seed=4, mixer='xy')
    assert len(sel) == 3
    assert np.isclose(d['qaoa_feasible_mass'], 1, atol=1e-7)
    assert d['qaoa_feasible_shots'] == 200


def test_x_qaoa_decodes_a_k_hot_string_and_reports_its_leak():
    Q = _rand_qubo(7, 22)
    sel, d = run_qaoa(Q, 3, reps=2, maxiter=20, shots=400, seed=4, mixer='x')
    assert len(sel) == 3
    assert 0 < d['qaoa_feasible_mass'] < 1
    assert 0 <= d['qaoa_optimal_mass'] <= 1 and 0 < d['uniform_optimal_mass'] <= 1


# ---------------------------------------------------------------- determinism
@pytest.mark.parametrize('method', ['anneal', 'random_khot', 'qaoa', 'qaoa_xy', 'greedy', 'milp_qubo'])
def test_same_seed_same_answer(method):
    inst = make_instance(8, 3, seed=7, regime='hard')
    cfg = OptConfig(**{**inst['cfg'].__dict__, 'qaoa_maxiter': 15, 'qaoa_shots': 64,
                       'anneal_steps': 50, 'anneal_restarts': 2})
    a, da = choose(method, inst['mu'], inst['cov'], inst['prev'], cfg, seed=5)
    b, db = choose(method, inst['mu'], inst['cov'], inst['prev'], cfg, seed=5)
    np.testing.assert_array_equal(a, b)
    timing = {'construct_seconds', 'solve_seconds', 'refine_seconds', 'runtime_seconds',
              'init_seconds', 'optimise_seconds', 'decode_seconds'}
    assert {k: v for k, v in da.items() if k not in timing} == {k: v for k, v in db.items() if k not in timing}


def test_stochastic_solvers_seeded_when_budget_is_far_below_search_space():
    # 16 shots over C(30,6)=593,775 supports: an unseeded sampler returns a different best almost surely.
    Q = _rand_qubo(30, 77)
    np.testing.assert_array_equal(random_khot(Q, 6, shots=16, seed=3), random_khot(Q, 6, shots=16, seed=3))
    assert len({tuple(random_khot(Q, 6, shots=16, seed=s)) for s in range(6)}) > 1
    np.testing.assert_array_equal(anneal_qubo(Q, 6, 30, 2, seed=3), anneal_qubo(Q, 6, 30, 2, seed=3))


def test_greedy_returns_a_true_swap_local_optimum():
    for seed in range(8):
        Q = _rand_qubo(9, 200 + seed)
        sel = set(greedy_swap(Q, 3).tolist())
        e = qubo_energy(Q, np.array(sorted(sel)))
        for i in sel:
            for j in set(range(9)) - sel:
                assert qubo_energy(Q, np.array(sorted(sel - {i} | {j}))) >= e - 1e-12


@pytest.mark.parametrize('mixer', ['x', 'xy'])
def test_qaoa_decodes_lowest_true_energy_sample(mixer):
    # 5 assets, k=2: 10 feasible strings; 2000 shots sample every one with overwhelming probability,
    # so decoding by TRUE energy must return the exact optimum.
    for seed in range(4):
        Q = _rand_qubo(5, 300 + seed)
        sel, _ = run_qaoa(Q, 2, reps=1, maxiter=5, shots=2000, seed=seed, mixer=mixer)
        assert np.isclose(qubo_energy(Q, sel), _brute(Q, 2))


def test_instances_are_seeded_and_psd():
    a = make_instance(20, 4, seed=3, regime='hard')
    b = make_instance(20, 4, seed=3, regime='hard')
    np.testing.assert_array_equal(a['mu'], b['mu'])
    np.testing.assert_array_equal(a['cov'], b['cov'])
    assert np.linalg.eigvalsh(a['cov']).min() > 0
    assert not np.array_equal(make_instance(20, 4, seed=4, regime='hard')['mu'], a['mu'])


def test_anneal_random_greedy_find_optimum_on_easy_small_instance():
    Q = _rand_qubo(6, 30)
    ref = _brute(Q, 2)
    assert np.isclose(qubo_energy(Q, random_khot(Q, 2, shots=2000, seed=1)), ref)
    assert np.isclose(qubo_energy(Q, anneal_qubo(Q, 2, 200, 3, seed=1)), ref)
    assert qubo_energy(Q, greedy_swap(Q, 2)) >= ref - 1e-12


# ---------------------------------------------------------------- the plan records what it will not run
def test_scaling_plan_refuses_statevector_qaoa_beyond_limit_with_reason():
    plan = plan_runs(sizes=[6, 30, 100], regimes=['hard'], seeds=[0], methods=['qaoa', 'qaoa_xy', 'milp_qubo', 'exact_qubo'])
    by = {(r['n'], r['method']): r for r in plan}
    assert by[(6, 'qaoa')]['status'] == 'run'
    assert by[(30, 'qaoa')]['status'] == 'not_run' and 'GB' in by[(30, 'qaoa')]['reason']
    assert by[(100, 'qaoa_xy')]['status'] == 'not_run'
    assert by[(100, 'milp_qubo')]['status'] == 'run'
    assert by[(100, 'exact_qubo')]['status'] == 'not_run' and 'C(100,20)' in by[(100, 'exact_qubo')]['reason']


# ---------------------------------------------------------------- audit findings O1, O3, O4 (research-audit)
@pytest.mark.parametrize('mixer', ['x', 'xy'])
def test_qaoa_reports_same_shot_uniform_baseline_and_approx_ratio(mixer):
    """O1: a QAOA row must carry the uniform sampler's numbers for the SAME shot budget."""
    n, k, shots = 7, 3, 50
    Q = _rand_qubo(n, 41)
    _, d = run_qaoa(Q, k, reps=2, maxiter=20, shots=shots, seed=2, mixer=mixer)
    E = np.array([qubo_energy(Q, np.array(s)) for s in combinations(range(n), k)])
    space = (1 << n) if mixer == 'x' else comb(n, k)
    n_opt = int(np.isclose(E, E.min()).sum())
    assert np.isclose(d['uniform_optimal_mass'], n_opt / space)
    assert np.isclose(d['uniform_p_hit_in_shots'], 1 - (1 - n_opt / space) ** shots)
    assert np.isclose(d['qaoa_p_hit_in_shots'], 1 - (1 - d['qaoa_optimal_mass']) ** shots)
    assert np.isclose(d['uniform_approx_ratio'], (E.max() - E.mean()) / (E.max() - E.min()))
    # Recompute the circuit's own numbers independently from the reported angles.
    Q_cost = penalised_qubo(Q, k, cardinality_penalty(Q)) if mixer == 'x' else Q
    qc, betas, gammas, _, _ = qaoa_circuit(Q_cost, k, 2, mixer)
    params = [float(v) for v in d['qaoa_params'].split(';')]
    p = Statevector(qc.assign_parameters(dict(zip(list(betas) + list(gammas), params)))).probabilities()
    idx = [sum(1 << i for i in s) for s in combinations(range(n), k)]
    pf = p[idx] / p[idx].sum()
    assert np.isclose(d['qaoa_feasible_mass'], p[idx].sum(), atol=1e-9)
    assert np.isclose(d['qaoa_optimal_mass'], p[idx][np.isclose(E, E.min())].sum(), atol=1e-9)
    assert np.isclose(d['qaoa_approx_ratio'], (E.max() - pf @ E) / (E.max() - E.min()), atol=1e-9)


def test_full_exact_cap_is_one_number_for_reference_and_solver():
    """O3: C(10,3)=120 was refused by choose('full_exact') (cap 100) while the benchmark reference allowed 150."""
    import inspect
    from qc_trade import benchmark
    inst = make_instance(10, 3, seed=0, regime='trading')
    w, _ = choose('full_exact', inst['mu'], inst['cov'], inst['prev'], inst['cfg'], seed=0)
    assert np.count_nonzero(w > 1e-9) == 3
    assert 'max_cases=' not in inspect.getsource(benchmark.benchmark_solvers)


def test_milp_time_out_is_recorded_not_crashed():
    """O4: HiGHS hitting its time limit must return an UNCERTIFIED answer or a clear RuntimeError."""
    inst = make_instance(100, 20, seed=0, regime='hard')
    Q = qubo_matrix(inst['mu'], inst['cov'], inst['prev'], inst['cfg'])
    try:
        sel, info = milp_qubo(Q, 20, time_limit=0.05)
    except RuntimeError as err:
        assert 'no feasible' in str(err)
        return
    assert len(sel) == 20 and not info['milp_certified'] and 'milp_gap' in info


def test_milp_incumbent_without_gap_is_uncertified_not_typeerror(monkeypatch):
    """O4 exactly: HiGHS returns a solution but mip_gap=None (time limit, no bound)."""
    from scipy.optimize import OptimizeResult
    from qc_trade import optimizer
    Q = _rand_qubo(6, 50)

    def fake_milp(c, **kw):
        x = np.zeros(len(c)); x[:2] = 1
        return OptimizeResult(x=x, success=False, mip_gap=None, mip_node_count=None, message='Time limit reached')
    monkeypatch.setattr(optimizer, 'milp', fake_milp)
    sel, info = optimizer.milp_qubo(Q, 2)
    assert list(sel) == [0, 1] and info['milp_certified'] is False and np.isnan(info['milp_gap'])
