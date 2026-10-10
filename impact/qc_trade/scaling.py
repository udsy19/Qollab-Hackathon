"""Computational scaling study: QUBO solvers on SYNTHETIC instances of growing size.

This is a computational benchmark, NOT a trading result. Instances are
seeded synthetic factor-model problems (labelled ``synthetic`` in every
output). QAOA is ideal statevector simulation on a CPU (qiskit-aer), not
quantum hardware.

Two regimes:

* ``trading``  k = 3 positions, risk aversion 6, 4 bps turnover prior - the
               settings the intraday backtest uses (spec section 4: 2-3 positions).
* ``hard``     k = max(2, n // 5), risk aversion calibrated so the covariance
               term is as large as the return term - a combinatorially harder
               regime, so the comparison is not decided by an easy instance.

Every (n, regime, instance, method, solver seed) runs in a FRESH process, so
peak RSS is attributable to that one solve. Rows are appended to a JSONL
checkpoint as they finish; a rerun skips completed rows.

    python -m qc_trade.scaling --out outputs/scaling --workers 3
"""
from __future__ import annotations
import argparse
import json
import os
import platform
import resource
import sys
import tracemalloc
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from math import comb, log
from multiprocessing import get_context
from pathlib import Path
from time import perf_counter
import numpy as np

SIZES = [6, 10, 15, 20, 30, 50, 100]
REGIMES = ['trading', 'hard']
METHODS = ['exact_qubo', 'milp_qubo', 'greedy', 'anneal', 'random_khot', 'qaoa', 'qaoa_xy', 'full_exact']
STOCHASTIC = {'anneal', 'random_khot', 'qaoa', 'qaoa_xy'}
EXACT_CAP = 1_000_000          # supports enumerated by exact_qubo
FULL_EXACT_CAP = 2_000         # supports each refined by SLSQP for the full-objective reference
QAOA_RUN_MAX_N = 20            # largest statevector QAOA actually run (time budget, see reason())
MEMORY_BUDGET_GB = 4.0         # owner's cap for this shared laptop
SEC_PER_EVAL_N20 = 0.43        # measured: one Aer statevector evaluation, n=20, p=2, 1 thread


def k_for(n: int, regime: str) -> int:
    return 3 if regime == 'trading' else max(2, n // 5)


def make_instance(n: int, k: int, seed: int, regime: str) -> dict:
    """Seeded synthetic 30-minute-horizon instance: 1 market + 4 sector factors + idiosyncratic risk."""
    from .optimizer import OptConfig
    rng = np.random.default_rng([seed, n, k, REGIMES.index(regime)])
    beta = rng.uniform(.6, 1.4, n)
    sector = rng.integers(0, 4, n)
    load = np.zeros((n, 4))
    load[np.arange(n), sector] = rng.uniform(.5, 1.5, n)
    idio = rng.uniform(8e-4, 3e-3, n)
    cov = (2e-3 ** 2) * np.outer(beta, beta) + (1.2e-3 ** 2) * load @ load.T + np.diag(idio ** 2)
    mu = rng.normal(0, 4e-4, n)
    prev = np.zeros(n)
    prev[rng.choice(n, size=k, replace=False)] = 1 / k
    if regime == 'trading':
        gamma = 6.0
    else:
        sig2 = float(np.mean(np.diag(cov)))
        off = float((cov.sum() - np.trace(cov)) / (n * (n - 1)))
        gamma = 2 * float(np.std(mu)) / (sig2 / k + (k - 1) / k * off)
    cfg = OptConfig(k=k, risk_aversion=gamma, min_weight=.03, max_weight=.8, expected_cost_bps=4.0,
                    anneal_steps=50 * n, anneal_restarts=4, qaoa_reps=2, qaoa_maxiter=80,
                    qaoa_shots=1024, milp_time_limit=60.0, seed=seed)
    return {'mu': mu, 'cov': cov, 'prev': prev, 'cfg': cfg, 'data': 'synthetic'}


def reason(n: int, k: int, method: str) -> str | None:
    """Why a configuration is NOT run, or None if it is."""
    if method == 'exact_qubo' and comb(n, k) > EXACT_CAP:
        return f'C({n},{k})={comb(n, k):.3g} supports exceeds the {EXACT_CAP:.0e} enumeration cap'
    if method == 'full_exact' and comb(n, k) > FULL_EXACT_CAP:
        return f'C({n},{k})={comb(n, k):.3g} SLSQP refinements exceeds the {FULL_EXACT_CAP} cap'
    if method in {'qaoa', 'qaoa_xy'} and n > QAOA_RUN_MAX_N:
        gb = (1 << n) * 16 / 1e9
        if gb > MEMORY_BUDGET_GB:
            return (f'statevector needs 2^{n} x 16 B = {gb:.3g} GB (one copy) > {MEMORY_BUDGET_GB:g} GB budget')
        est = SEC_PER_EVAL_N20 * 2 ** (n - 20) * (n / 20) ** 2 * 80
        return (f'statevector fits ({gb:.3g} GB) but ~{est / 60:.0f} min per run (80 evaluations, '
                f'extrapolated from {SEC_PER_EVAL_N20} s/eval at n=20) exceeds the time budget')
    return None


def plan_runs(sizes=SIZES, regimes=REGIMES, seeds=(0, 1, 2), methods=METHODS, solver_seeds=(0, 1, 2)) -> list[dict]:
    rows = []
    for regime in regimes:
        for n in sizes:
            k = k_for(n, regime)
            for seed in seeds:
                for method in methods:
                    why = reason(n, k, method)
                    for s in (solver_seeds if method in STOCHASTIC else (0,)):
                        rows.append({'n': n, 'k': k, 'regime': regime, 'instance': seed, 'method': method,
                                     'solver_seed': s, 'status': 'not_run' if why else 'run', 'reason': why or ''})
    return rows


def _key(r: dict) -> tuple:
    return (r['regime'], r['n'], r['instance'], r['method'], r['solver_seed'])


def _peak_rss_mb() -> float:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / 1e6 if sys.platform == 'darwin' else peak / 1e3


def run_one(task: dict) -> dict:
    """Run one solve in this (fresh) process and measure it end to end."""
    from .optimizer import choose, portfolio_objective
    inst = make_instance(task['n'], task['k'], task['instance'], task['regime'])
    mu, cov, prev, cfg = inst['mu'], inst['cov'], inst['prev'], inst['cfg']
    rss_before = _peak_rss_mb()
    tracemalloc.start()
    row = {**task, 'data': 'synthetic', 'risk_aversion': cfg.risk_aversion}
    tick = perf_counter()
    try:
        w, d = choose(task['method'], mu, cov, prev, cfg, seed=1000 * task['instance'] + task['solver_seed'])
        wall = perf_counter() - tick
        support = np.flatnonzero(w > 1e-9)
        row.update({k: v for k, v in d.items() if isinstance(v, (int, float, str, bool, np.floating, np.integer))})
        row.update({'feasible': bool(len(support) == cfg.k and abs(w.sum() - 1) < 1e-6
                                     and w[support].min() >= cfg.min_weight - 1e-6
                                     and w.max() <= cfg.max_weight + 1e-6),
                    'support': ';'.join(map(str, support)),
                    'portfolio_objective': portfolio_objective(w, mu, cov, prev, cfg),
                    'wall_seconds': wall, 'error': ''})
        if task['method'] == 'full_exact':
            from .optimizer import qubo_matrix, qubo_energy
            row['qubo_energy'] = qubo_energy(qubo_matrix(mu, cov, prev, cfg), support)
    except Exception as err:  # recorded, never swallowed: the row says it failed and why
        row.update({'feasible': False, 'wall_seconds': perf_counter() - tick, 'error': repr(err)[:200]})
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    row['tracemalloc_peak_mb'] = peak / 1e6
    row['peak_rss_mb'] = _peak_rss_mb()
    row['rss_growth_mb'] = max(0.0, row['peak_rss_mb'] - rss_before)
    return {k: (v.item() if isinstance(v, np.generic) else v) for k, v in row.items()}


def _warm(_=None):
    import qc_trade.optimizer  # noqa: F401  (imports qiskit + aer before the baseline RSS reading)


def _run_isolated(task):
    _warm()
    return run_one(task)


def execute(out: Path, workers: int, plan: list[dict]) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    ckpt = out / 'trials.jsonl'
    done = set()
    if ckpt.exists():
        done = {_key(json.loads(line)) for line in ckpt.read_text().splitlines() if line.strip()}
    todo = [r for r in plan if r['status'] == 'run' and _key(r) not in done]
    # Expensive first so the long QAOA/MILP solves overlap with the many cheap ones.
    todo.sort(key=lambda r: (r['method'] not in {'qaoa', 'qaoa_xy', 'milp_qubo'}, -r['n']))
    print(f'{len(done)} rows checkpointed, {len(todo)} to run, {workers} workers', flush=True)
    ctx = get_context('spawn')
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx, max_tasks_per_child=1) as pool, \
            ckpt.open('a') as fh:
        futures = {pool.submit(_run_isolated, t): t for t in todo}
        for i, f in enumerate(as_completed(futures), 1):
            row = f.result()
            fh.write(json.dumps(row) + '\n')
            fh.flush()
            if i % 25 == 0 or row['method'] in {'qaoa', 'qaoa_xy'}:
                print(f'[{i}/{len(todo)}] {row["regime"]} n={row["n"]} {row["method"]} '
                      f'{row.get("wall_seconds", 0):.2f}s {row.get("error", "")}', flush=True)
    return ckpt


def summarise(out: Path, plan: list[dict]):
    """References, gaps, time-to-target, the not-run table, and the summary."""
    import pandas as pd
    trials = pd.DataFrame([json.loads(x) for x in (out / 'trials.jsonl').read_text().splitlines() if x.strip()])
    ok = trials[trials.feasible & (trials.error == '')]
    refs = []
    for (regime, n, inst), g in trials.groupby(['regime', 'n', 'instance']):
        ex = g[(g.method == 'exact_qubo') & g.feasible]
        ml = g[(g.method == 'milp_qubo') & g.feasible & (g.get('milp_certified', False) == True)]  # noqa: E712
        if len(ex):
            q_ref, q_kind = float(ex.qubo_energy.min()), 'exact_enumeration'
        elif len(ml):
            q_ref, q_kind = float(ml.qubo_energy.min()), 'milp_certified'
        else:
            q_ref, q_kind = float(ok[(ok.regime == regime) & (ok.n == n) & (ok.instance == inst)].qubo_energy.min()), 'best_known'
        fe = g[(g.method == 'full_exact') & g.feasible]
        gg = ok[(ok.regime == regime) & (ok.n == n) & (ok.instance == inst)]
        p_ref, p_kind = ((float(fe.portfolio_objective.min()), 'full_enumeration') if len(fe)
                         else (float(gg.portfolio_objective.min()), 'best_known'))
        refs.append({'regime': regime, 'n': n, 'instance': inst, 'qubo_ref': q_ref, 'qubo_ref_kind': q_kind,
                     'portfolio_ref': p_ref, 'portfolio_ref_kind': p_kind})
    refs = pd.DataFrame(refs)
    t = trials.merge(refs, on=['regime', 'n', 'instance'])
    scale = t.qubo_ref.abs().clip(lower=1e-12)
    t['qubo_gap_rel'] = (t.qubo_energy - t.qubo_ref) / scale
    t['portfolio_gap_bps'] = (t.portfolio_objective - t.portfolio_ref) * 1e4
    t['hit_target'] = t.feasible & (t.qubo_gap_rel <= 1e-9)
    t.to_csv(out / 'trials.csv', index=False)

    def ttt99(g):
        p = g.hit_target.mean()
        med = g.runtime_seconds.median()
        if p == 0:
            return np.inf
        return med if p >= 1 else med * log(0.01) / log(1 - p)

    def seed_std(g):
        s = g.groupby('instance').qubo_gap_rel.std(ddof=0)
        return float(s.mean()) if len(s) else np.nan

    rows = []
    for (regime, n, method), g in t.groupby(['regime', 'n', 'method']):
        rows.append({'regime': regime, 'n': n, 'k': int(g.k.iloc[0]), 'method': method, 'runs': len(g),
                     'feasible_rate': g.feasible.mean(), 'hit_rate': g.hit_target.mean(),
                     'qubo_ref_kind': '/'.join(sorted(set(g.qubo_ref_kind))),
                     'median_qubo_gap_rel': g.qubo_gap_rel.median(), 'max_qubo_gap_rel': g.qubo_gap_rel.max(),
                     'median_portfolio_gap_bps': g.portfolio_gap_bps.median(),
                     'max_portfolio_gap_bps': g.portfolio_gap_bps.max(),
                     'median_runtime_s': g.runtime_seconds.median(), 'p95_runtime_s': g.runtime_seconds.quantile(.95),
                     'median_solve_s': g.solve_seconds.median(), 'median_refine_s': g.refine_seconds.median(),
                     'ttt99_s': ttt99(g), 'seed_std_qubo_gap_rel': seed_std(g),
                     'median_rss_growth_mb': g.rss_growth_mb.median(), 'max_peak_rss_mb': g.peak_rss_mb.max(),
                     'median_tracemalloc_mb': g.tracemalloc_peak_mb.median(),
                     'milp_certified_rate': g['milp_certified'].mean() if 'milp_certified' in g and method == 'milp_qubo' else np.nan,
                     'qaoa_optimal_mass': g['qaoa_optimal_mass'].median() if 'qaoa_optimal_mass' in g else np.nan,
                     'uniform_optimal_mass': g['uniform_optimal_mass'].median() if 'uniform_optimal_mass' in g else np.nan,
                     'qaoa_feasible_mass': g['qaoa_feasible_mass'].median() if 'qaoa_feasible_mass' in g else np.nan,
                     'errors': int((g.error != '').sum())})
    summary = pd.DataFrame(rows).sort_values(['regime', 'n', 'method'])
    summary.to_csv(out / 'summary.csv', index=False)
    not_run = pd.DataFrame([r for r in plan if r['status'] == 'not_run'],
                           columns=['regime', 'n', 'k', 'method', 'reason']).drop_duplicates(['regime', 'n', 'method'])
    not_run.to_csv(out / 'not_run.csv', index=False)
    return t, summary, not_run


COLORS = {'exact_qubo': '#2a78d6', 'milp_qubo': '#eb6834', 'greedy': '#1baf7a', 'anneal': '#eda100',
          'random_khot': '#e87ba4', 'qaoa': '#6250d6', 'qaoa_xy': '#e34948', 'full_exact': '#008300'}
MARKERS = {'exact_qubo': 'o', 'milp_qubo': 's', 'greedy': '^', 'anneal': 'v', 'random_khot': 'x',
           'qaoa': 'D', 'qaoa_xy': 'P', 'full_exact': '*'}


def plot(out: Path, summary, not_run) -> list[Path]:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    paths = []
    panels = [('median_runtime_s', 'median end-to-end runtime (s, log)', True),
              ('ttt99_s', 'time-to-target, 99% (s, log; missing = never hit)', True),
              ('max_peak_rss_mb', 'peak process RSS (MB, log)', True),
              ('median_qubo_gap_rel', 'median relative QUBO gap to reference', False)]
    for regime in REGIMES:
        s = summary[(summary.regime == regime) & (summary.method != 'full_exact')]
        if s.empty:
            continue
        fig, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
        for ax, (col, label, logy) in zip(axes.flat, panels):
            for method in [m for m in METHODS if m in set(s.method)]:
                g = s[s.method == method].sort_values('n')
                y = g[col].replace([np.inf], np.nan)
                ax.plot(g.n, y, color=COLORS[method], marker=MARKERS[method], lw=2, ms=7, label=method)
            ax.set_xscale('log')
            ax.set_xticks(SIZES, [str(x) for x in SIZES])
            ax.minorticks_off()
            if logy:
                ax.set_yscale('log')
            ax.set_xlabel('assets N')
            ax.set_ylabel(label)
            ax.grid(alpha=.25, lw=.6)
            for side in ('top', 'right'):
                ax.spines[side].set_visible(False)
        axes.flat[0].legend(frameon=False, fontsize=8, ncol=2)
        nr = not_run[(not_run.regime == regime) & not_run.method.isin(['qaoa', 'qaoa_xy'])]
        cut = f"QAOA not run for N in {sorted(set(nr.n))} (see not_run.csv)" if len(nr) else ''
        fig.suptitle(f'QUBO solver scaling - SYNTHETIC instances, regime "{regime}" '
                     f'(k = {"3" if regime == "trading" else "max(2, N//5)"}). '
                     f'QAOA = ideal CPU statevector simulation, not hardware. {cut}', fontsize=9)
        p = out / f'scaling_{regime}.png'
        fig.savefig(p, dpi=130)
        plt.close(fig)
        paths.append(p)
    q = summary[summary.method.isin(['qaoa', 'qaoa_xy'])].dropna(subset=['qaoa_optimal_mass'])
    if len(q):
        fig, ax = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
        for (regime, method), g in q.groupby(['regime', 'method']):
            g = g.sort_values('n')
            ax.plot(g.n, g.qaoa_optimal_mass / g.uniform_optimal_mass, color=COLORS[method], marker=MARKERS[method],
                    ls='-' if regime == 'hard' else '--', lw=2, ms=7, label=f'{method}, {regime}')
        ax.axhline(1, color='#52514e', lw=1, ls=':')
        ax.set_yscale('log')
        ax.set_xlabel('assets N')
        ax.set_ylabel('P(optimal) after QAOA / P(optimal) uniform start')
        ax.set_title('QAOA amplification of the optimal portfolio over its own start state (p = 2, ideal)', fontsize=9)
        ax.legend(frameon=False, fontsize=8)
        ax.grid(alpha=.25, lw=.6)
        p = out / 'qaoa_amplification.png'
        fig.savefig(p, dpi=130)
        plt.close(fig)
        paths.append(p)
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default='outputs/scaling')
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--sizes', type=int, nargs='+', default=SIZES)
    ap.add_argument('--instances', type=int, default=3)
    ap.add_argument('--summarise-only', action='store_true')
    a = ap.parse_args(argv)
    for var in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        os.environ[var] = '1'  # single-threaded solves: fair comparison, moderate CPU on a shared laptop
    out = Path(a.out)
    plan = plan_runs(sizes=a.sizes, seeds=tuple(range(a.instances)))
    if not a.summarise_only:
        execute(out, a.workers, plan)
    t, summary, not_run = summarise(out, plan)
    paths = plot(out, summary, not_run)
    import qiskit, qiskit_aer, scipy
    (out / 'manifest.json').write_text(json.dumps({
        'data': 'synthetic (seeded factor model) - computational benchmark, not a trading result',
        'simulator': 'qiskit-aer statevector, ideal, CPU, 1 thread - NOT quantum hardware',
        'python': platform.python_version(), 'machine': platform.platform(), 'numpy': np.__version__,
        'scipy': scipy.__version__, 'qiskit': qiskit.__version__, 'qiskit_aer': qiskit_aer.__version__,
        'sizes': a.sizes, 'instances': a.instances, 'workers': a.workers, 'methods': METHODS,
        'plan_rows': len(plan), 'trial_rows': len(t), 'not_run_configs': len(not_run),
        'config_example': {r: asdict(make_instance(10, k_for(10, r), 0, r)['cfg']) for r in REGIMES},
        'outputs': [p.name for p in paths] + ['trials.jsonl', 'trials.csv', 'summary.csv', 'not_run.csv'],
    }, indent=2, default=str))
    print(summary.to_string(index=False))


if __name__ == '__main__':
    main()
