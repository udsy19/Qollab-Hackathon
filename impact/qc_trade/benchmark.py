"""Reproducible, same-instance QUBO/QAOA/classical comparisons.

This is computational benchmarking, not an estimate of trading alpha.
QAOA is noiseless exponential statevector simulation. It is NOT IBM hardware.
"""
from __future__ import annotations
from dataclasses import replace
from itertools import combinations
from math import comb
import numpy as np
import pandas as pd
from .data import BarPanel
from .backtest import ExecutionConfig, closed_bar_returns, signal_positions, forecast
from .optimizer import (OptConfig,choose,full_exact,qubo_matrix,exact_qubo,
                        qubo_energy,portfolio_objective)


def benchmark_solvers(panel: BarPanel, e: ExecutionConfig, o: OptConfig, *,
                      counts: list[int]|None=None, max_snapshots=6, restarts=3,
                      include_qaoa=True) -> tuple[pd.DataFrame,pd.DataFrame]:
    """Sample snapshots deterministically throughout OUT-OF-SAMPLE timeline.

    Each instance fixes exactly the same mu/Cov/previous holdings for solvers.
    Includes full support+convex weight optimum as the portfolio objective
    reference, unlike QUBO-only exact enumeration.
    """
    n_all = len(panel.close.columns)
    sizes = counts or [c for c in [4,6,8] if c <= n_all]
    sizes = sorted(set(x for x in sizes if 2 <= x <= n_all))
    if not sizes:
        sizes = [n_all]
    returns = closed_bar_returns(panel)
    observed = returns.dropna().to_numpy(float)
    cumulative = (~returns.isna().any(axis=1)).cumsum().to_numpy()
    candidate = [t for t in signal_positions(panel,e) if panel.days.iloc[t] >= e.test_start and
                 cumulative[t] >= e.history_bars]
    if not candidate:
        raise ValueError('No OOS decision snapshots with enough training data')
    selected = [candidate[i] for i in np.unique(np.linspace(0,len(candidate)-1,
                          num=min(max_snapshots,len(candidate)),dtype=int))]
    entries=[]
    for size in sizes:
        config = replace(o,k=min(o.k,size-1))
        if not config.k*config.min_weight <= 1 <= config.k*config.max_weight:
            continue
        for snap_idx,t in enumerate(selected):
            mu,cov = forecast(observed[cumulative[t]-e.history_bars:cumulative[t], :size],
                              horizon_bars=e.rebalance_minutes//5, shrinkage=e.alpha_shrinkage)
            # Two realistic previous-holding regimes; both stay fixed for every solver:
            # from-flat initial entry and a fully invested older support.
            for prev_kind in ('flat','invested'):
                prev = np.zeros(size)
                if prev_kind == 'invested':
                    prev[:config.k] = 1/config.k
                q = qubo_matrix(mu,cov,prev,config)
                exact_idx = exact_qubo(q,config.k)
                best_qubo = qubo_energy(q,exact_idx)
                true_best = full_exact(mu,cov,prev,config,max_cases=150) if comb(size,config.k)<=150 else None
                best_full = portfolio_objective(true_best,mu,cov,prev,config) if true_best is not None else np.nan
                modes = ['exact_qubo','milp_qubo','greedy','anneal','topk']
                if true_best is not None:
                    modes += ['full_exact']
                if include_qaoa and size <= 9:
                    modes += ['qaoa','qaoa_xy']
                for mode in modes:
                    trials = restarts if mode in {'anneal','qaoa','qaoa_xy','greedy','exact_qubo','milp_qubo'} else 1
                    for j in range(trials):
                        seed = config.seed + 100_000*size + 1000*snap_idx + 10*(prev_kind=='invested') + j
                        try:
                            w,detail = choose(mode,mu,cov,prev,config,seed=seed)
                            support = np.flatnonzero(w > 1e-5)
                            objective = portfolio_objective(w,mu,cov,prev,config)
                            gap = objective-best_full
                            qgap = qubo_energy(q,support)-best_qubo
                            good = len(support)==config.k and abs(w.sum()-1)<1e-5
                            error = ''
                        except Exception as err:
                            detail = {}
                            gap, qgap, good = np.nan,np.nan,False
                            error = str(err)[:180]
                        entries.append({'n':size,'k':config.k,'snapshot':snap_idx,
                          'signal_time_utc':(panel.close.index[t]+pd.Timedelta(minutes=5)).isoformat(),
                          'prev_type':prev_kind,'method':mode,'seed':seed,
                          'feasible':good,'seconds_total':detail.get('runtime_seconds',np.nan),
                          'qubo_gap_to_exact':qgap,'portfolio_gap_to_full_exact':gap,
                          'qaoa_feasible_mass':detail.get('qaoa_feasible_mass',np.nan),
                          'qaoa_feasible_shots':detail.get('qaoa_feasible_shots',np.nan),
                          'qaoa_parameter_evals':detail.get('qaoa_evaluations',np.nan),
                          'milp_gap':detail.get('milp_gap',np.nan),
                          'milp_certified':detail.get('milp_certified',np.nan),
                          'qaoa_state_dimension':2**size if mode in {'qaoa','qaoa_xy'} else np.nan,
                          'error':error})
    detailed = pd.DataFrame(entries)
    summary = (detailed.groupby(['n','k','method'],as_index=False)
      .agg(trials=('feasible','size'),feasibility_rate=('feasible','mean'),
           median_seconds=('seconds_total','median'),p95_seconds=('seconds_total',lambda v:v.quantile(.95)),
           median_qubo_gap=('qubo_gap_to_exact','median'),
           median_refined_gap=('portfolio_gap_to_full_exact','median'),
           worst_refined_gap=('portfolio_gap_to_full_exact','max'),
           mean_qaoa_feasible_mass=('qaoa_feasible_mass','mean')))
    return detailed,summary
