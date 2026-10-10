"""Audit measurements (synthetic inputs, NOT market evidence).
1. Backtest runtime vs number of sessions (performance bottleneck).
2. QAOA benchmark: does sampling alone find the QUBO optimum? Compare optimized QAOA,
   QAOA with its parameter search disabled (maxiter=1), and uniform random K-hot sampling,
   all with the benchmark's shot count, on random QUBOs."""
import time
from itertools import combinations
import numpy as np
from qc_trade.demo import synthetic_panel
from qc_trade.optimizer import OptConfig, exact_qubo, qubo_energy, qaoa_xy_statevector, qaoa_statevector
from qc_trade.backtest import ExecutionConfig, run_backtest

print('== 1. runtime, 6 symbols, methods milp_qubo,exact_qubo,greedy,topk,minvar,spy,equal,cash')
for start, end, ts in [('2026-07-01', '2026-07-31', '2026-07-15'), ('2026-06-01', '2026-08-31', '2026-08-01')]:
    p = synthetic_panel(start=start, end=end)
    e = ExecutionConfig(test_start=ts, history_bars=80)
    t0 = time.perf_counter()
    run_backtest(p, e, OptConfig(k=2), ['milp_qubo', 'exact_qubo', 'greedy', 'topk', 'minvar', 'spy', 'equal', 'cash'])
    dt = time.perf_counter() - t0
    sessions = p.days.nunique()
    print(f'sessions={sessions} bars={len(p.close)} seconds={dt:.1f} sec_per_session={dt/sessions:.3f}')

print('== 2. QAOA vs sampling, n=6 k=2 (15 feasible states), shots as in the demo benchmark (256)')
rng = np.random.default_rng(0)
rows = []
for trial in range(20):
    n, k = 6, 2
    q = rng.normal(size=(n, n)); q = (q + q.T) / 2
    best = qubo_energy(q, exact_qubo(q, k))
    opt = OptConfig(k=k, qaoa_maxiter=35, qaoa_shots=256)
    frozen = OptConfig(k=k, qaoa_maxiter=1, qaoa_shots=256)
    xy, xyd = qaoa_xy_statevector(q, k, opt, seed=trial)
    xy0, _ = qaoa_xy_statevector(q, k, frozen, seed=trial)
    x, xd = qaoa_statevector(q, k, opt, seed=trial)
    supports = list(combinations(range(n), k))
    draws = rng.integers(0, len(supports), 256)
    rand_best = min(qubo_energy(q, np.array(supports[d])) for d in draws)
    # probability mass QAOA-XY puts on the optimum is the quantity that would matter at scale
    rows.append((qubo_energy(q, xy) - best, qubo_energy(q, xy0) - best, qubo_energy(q, x) - best, rand_best - best,
                 xyd['qaoa_feasible_mass'], xd['qaoa_feasible_mass']))
r = np.array(rows)
print(f'trials=20 optimum_found: qaoa_xy={np.mean(np.isclose(r[:,0],0)):.2f} '
      f'qaoa_xy_no_param_search={np.mean(np.isclose(r[:,1],0)):.2f} qaoa_x={np.mean(np.isclose(r[:,2],0)):.2f} '
      f'uniform_random_256_samples={np.mean(np.isclose(r[:,3],0)):.2f}')
print(f'P(uniform 256 draws over 15 states miss the optimum) = {(14/15)**256:.2e}')
print(f'mean X-mixer feasible mass={r[:,5].mean():.3f}')
