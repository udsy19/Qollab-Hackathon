"""Portfolio Selection by QAOA: a skeptical benchmark. Pick k of n ETFs (a QUBO), solve it with two Qiskit QAOA
variants and four classical solvers on the SAME instance, and report objective, feasibility, gap and runtime.
On Qollab: press Run on Qollab, pick the Built-in simulator, press Run. The data are SYNTHETIC (see qctrade/instance.py).
"""
import json
from itertools import combinations
from math import comb
from time import perf_counter

import numpy as np
import qiskit
from qiskit import transpile

from qctrade.instance import load_stats, select_universe
from qctrade.qaoa import build_qaoa, decode_counts, tune_angles
from qctrade.solvers import (OptConfig, anneal_qubo, exact_qubo, greedy_swap, milp_qubo, portfolio_objective,
                             qubo_energy, qubo_matrix, refine)

try:
    backend  # Qollab pre-creates this from the Select QPU dialog; never replace it on Qollab
except NameError:  # off Qollab (local dev only): Qiskit's built-in simulator
    from qiskit.providers.basic_provider import BasicSimulator
    backend = BasicSimulator()

# The one data file. To run on real DERIVED statistics, drop a JSON with the same keys next to it and change this
# literal (Qollab loads only files whose path is written out as a plain string).
STATS_FILE = "data/etf_stats_synthetic.json"
ANGLE_STARTS = 3     # random COBYLA starts per QAOA variant (local Statevector only, no backend jobs)
ANGLE_MAXITER = 120  # COBYLA iterations per start


def _ms(seconds: float) -> str:
    return f"{seconds * 1e3:9.1f}"


def _names(tickers, idx) -> str:
    return "+".join(tickers[i] for i in idx) if idx is not None else "-"


def _row(name, sel, energy, feasible, gap, rel, secs, note=""):
    gap_s = f"{gap:10.5f}" if gap is not None else f"{'-':>10}"
    rel_s = f"{rel:7.2f}%" if rel is not None else f"{'-':>8}"
    e_s = f"{energy:10.5f}" if energy is not None else f"{'-':>10}"
    print(f"  {name:<22} {sel:<16} {e_s} {feasible:<9} {gap_s} {rel_s} {secs:>10}  {note}")


# Qollab calls main() itself and turns its parameters into a Run settings form. The signature must stay on ONE
# line at column 0 with every parameter annotated int/float/str/bool, or main() is silently never called.
# Never call main() from this file: on an IonQ backend a second call would be a second job and fail the run.
def main(n_assets: int = 6, k: int = 2, reps: int = 2, shots: int = 1024, seed: int = 7, risk_aversion: float = 6.0):
    t_start = perf_counter()
    backend_name = str(getattr(backend, "name", type(backend).__name__))
    print("=" * 100)
    print("Portfolio Selection by QAOA: a skeptical benchmark  (Qiskit " + qiskit.__version__ + ", backend: " + backend_name + ")")
    print("=" * 100)

    stats, origin = load_stats(STATS_FILE)
    tickers, mu, cov = select_universe(stats, n_assets)
    print(f"DATA: {stats.get('label', 'unlabelled')}  [{origin}]")
    if stats.get("synthetic"):
        print("      These numbers are SYNTHETIC. No result below is a market result or investment advice.")
    cfg = OptConfig(k=k, risk_aversion=risk_aversion)
    prev = np.zeros(n_assets)  # start from cash, so turnover cost is the same for every k-subset
    t0 = perf_counter()
    Q = qubo_matrix(mu, cov, prev, cfg)
    t_build = perf_counter() - t0
    print(f"PROBLEM: choose k={k} of n={n_assets} ETFs {tickers}; risk aversion {risk_aversion}; "
          f"{comb(n_assets, k)} feasible portfolios of {2 ** n_assets} bitstrings.")
    print("         QUBO E(y) = -mu'y/k + (gamma/2k^2) y'Cov y + turnover cost; lower is better. Built in "
          f"{t_build * 1e3:.2f} ms.")
    print("  " + "  ".join(f"{t}: mu={m:+.3f} vol={np.sqrt(v):.3f}" for t, m, v in zip(tickers, mu, np.diag(cov))))

    # ---- Classical solvers, each timed end to end on the same Q --------------------------------------------
    results = []

    def run_classical(name, fn):
        t = perf_counter()
        try:
            out = fn()
        except ImportError as err:
            results.append({"solver": name, "available": False, "why": f"not available here: {err}"})
            return
        sel, extra = out if isinstance(out, tuple) else (out, {})
        results.append({"solver": name, "available": True, "sel": np.sort(np.asarray(sel, int)),
                        "seconds": perf_counter() - t, **extra})

    run_classical("exact enumeration", lambda: exact_qubo(Q, k))
    run_classical("MILP (HiGHS)", lambda: milp_qubo(Q, k))
    run_classical("greedy + local swap", lambda: greedy_swap(Q, k))
    run_classical("simulated annealing", lambda: anneal_qubo(Q, k, cfg.anneal_steps, cfg.anneal_restarts, seed))
    opt_sel = results[0]["sel"]
    e_opt = qubo_energy(Q, opt_sel)

    # ---- QAOA: tune angles locally (exact Statevector, no jobs), then ONE backend.run for both circuits ------
    print(f"\nQAOA: tuning angles locally with Qiskit Statevector (reps={reps}, {ANGLE_STARTS} COBYLA starts, "
          f"<= {ANGLE_MAXITER} iterations each). This sends no jobs.")
    tuned = {m: tune_angles(Q, k, m, reps, ANGLE_MAXITER, ANGLE_STARTS, seed) for m in ("x", "xy")}
    for m, tr in tuned.items():
        print(f"  {m.upper():>2} mixer: {tr['evaluations']} statevector evaluations in {tr['tune_seconds']:.2f} s; "
              f"ideal feasible probability {tr['ideal_feasible_mass']:.3f}")
    circuits = [build_qaoa(tr["Q_scaled"], k, tr["gammas"], tr["betas"], m, measure=True) for m, tr in tuned.items()]
    t0 = perf_counter()
    compiled = transpile(circuits, backend=backend, optimization_level=1, seed_transpiler=seed)
    t_transpile = perf_counter() - t0
    for m, c in zip(tuned, compiled):
        ops = c.count_ops()
        two_q = sum(1 for inst in c.data if inst.operation.num_qubits == 2)
        print(f"  {m.upper():>2} circuit after transpile: {c.num_qubits} qubits, depth {c.depth()}, "
              f"{two_q} two-qubit gates, {sum(ops.values())} operations")
    print(f"Sending ONE job with both circuits ({shots} shots each) to {backend_name} ...")
    t0 = perf_counter()
    # ONE backend.run per run: IonQ backends accept exactly one job per run. Both circuits go in this call.
    # The built-in simulator takes a sampling seed, so a judge's run reproduces the numbers on the project page;
    # other backends get no extra option (an IonQ backend may reject unknown ones).
    run_options = {"seed_simulator": seed} if backend_name == "basic_simulator" else {}
    job_result = backend.run(compiled, shots=shots, **run_options).result()
    t_job = perf_counter() - t0
    print(f"  job finished in {t_job:.2f} s (shared by both circuits)")

    opt_index = int(sum(1 << int(i) for i in opt_sel))
    for i, (m, tr) in enumerate(tuned.items()):
        dec = decode_counts(job_result.get_counts(i), Q, k)
        counts_opt = dec["by_index"].get(opt_index, 0)
        results.append({
            "solver": f"QAOA {m.upper()} mixer" + (" + penalty" if m == "x" else ""), "available": True,
            "sel": dec["best"], "seconds": tr["tune_seconds"] + (t_transpile + t_job) / 2,
            "feasible_frac": dec["feasible_shots"] / max(dec["shots"], 1),
            "p_opt_sampled": counts_opt / max(dec["shots"], 1), "p_opt_ideal": float(tr["ideal_probs"][opt_index]),
            "most_frequent": dec["most_frequent"], "gammas": tr["gammas"].tolist(), "betas": tr["betas"].tolist(),
            "penalty": tr["penalty"]})

    # ---- Stage B: continuous sizing on each selected support, and the best portfolio over ALL supports ------
    t0 = perf_counter()
    best_full = min((portfolio_objective(refine(np.array(s), mu, cov, prev, cfg), mu, cov, prev, cfg), s)
                    for s in combinations(range(n_assets), k)) if comb(n_assets, k) <= 200 else None
    t_full = perf_counter() - t0
    for r in results:
        if r["available"] and r.get("sel") is not None and len(r["sel"]) == k:
            r["energy"] = qubo_energy(Q, r["sel"])
            r["gap"] = r["energy"] - e_opt
            r["rel_gap"] = 100 * r["gap"] / abs(e_opt) if e_opt else None
            w = refine(r["sel"], mu, cov, prev, cfg)
            r["weights"] = {tickers[i]: round(float(w[i]), 4) for i in r["sel"]}
            r["portfolio_objective"] = portfolio_objective(w, mu, cov, prev, cfg)

    # ---- Report ------------------------------------------------------------------------------------------
    print("\nRESULTS on one instance (stage A: QUBO selection). gap = E - E(exact); 0 means the certified optimum.")
    print(f"  {'solver':<22} {'selection':<16} {'QUBO E':>10} {'feasible':<9} {'gap':>10} {'rel.gap':>8} {'time ms':>10}  notes")
    for r in results:
        if not r["available"]:
            _row(r["solver"], "-", None, "-", None, None, "-", r["why"])
            continue
        if r.get("sel") is None:
            _row(r["solver"], "none", None, "no", None, None, _ms(r["seconds"]), "no feasible sample")
            continue
        note = ""
        if "feasible_frac" in r:
            feas = f"{100 * r['feasible_frac']:.1f}%"
            note = (f"best of {shots} shots; P(optimum) sampled {r['p_opt_sampled']:.3f}, ideal {r['p_opt_ideal']:.3f}; "
                    f"most frequent {_names(tickers, r['most_frequent'])}")
        else:
            feas = "yes"
            if "milp_certified" in r:
                note = "certified" if r["milp_certified"] else f"gap {r['milp_gap']}"
        _row(r["solver"], _names(tickers, r["sel"]), r["energy"], feas, r["gap"], r["rel_gap"], _ms(r["seconds"]), note)
    print(f"  baseline: a uniformly random k-subset is optimal with probability 1/C({n_assets},{k}) = {1 / comb(n_assets, k):.3f}; "
          f"a uniformly random bitstring is a feasible optimum with probability 1/2^{n_assets} = {1 / 2 ** n_assets:.4f}.")
    print("  QAOA time = local angle tuning (classical simulation) + half the shared transpile and job time. It is NOT a")
    print("  quantum hardware runtime, and no quantum speedup is claimed or measured here.")

    print("\nSTAGE B (continuous sizing by SLSQP on the chosen support; weights in [3%, 80%], fully invested):")
    for r in results:
        if r.get("portfolio_objective") is not None:
            vs = f"  (+{r['portfolio_objective'] - best_full[0]:.6f} vs best support)" if best_full else ""
            print(f"  {r['solver']:<22} objective {r['portfolio_objective']:+.6f}{vs}  weights {r['weights']}")
    if best_full:
        print(f"  best over ALL {comb(n_assets, k)} supports: objective {best_full[0]:+.6f} on {_names(tickers, best_full[1])} "
              f"({t_full * 1e3:.0f} ms). The QUBO scores equal weights, so its optimum need not be the best after sizing.")

    q_rows = [r for r in results if "feasible_frac" in r]
    c_rows = [r for r in results if r["available"] and "feasible_frac" not in r and r.get("gap") is not None]
    print("\nVERDICT (computed from the table above, this instance only):")
    print(f"  classical solvers reaching the optimum: {sum(abs(r['gap']) < 1e-12 for r in c_rows)} of {len(c_rows)}, "
          f"slowest {max(r['seconds'] for r in c_rows) * 1e3:.1f} ms.")
    for r in q_rows:
        hit = r.get("gap") is not None and abs(r["gap"]) < 1e-12
        print(f"  {r['solver']}: best sample {'IS' if hit else 'is NOT'} the optimum; "
              f"{100 * r['feasible_frac']:.1f}% of shots feasible; P(optimum) {r['p_opt_sampled']:.3f} "
              f"vs {1 / comb(n_assets, k):.3f} for a random k-subset; {r['seconds']:.2f} s.")
    print("  At this size exhaustive search is trivial, so QAOA cannot beat exhaustive search here; the question this run")
    print("  answers is how much probability QAOA puts on the optimum, and at what cost, against honest baselines.")
    print(f"\nTotal run time {perf_counter() - t_start:.1f} s. Jobs sent to the backend: 1.")

    summary = {"data_label": stats.get("label"), "synthetic": bool(stats.get("synthetic")), "backend": backend_name,
               "qiskit": qiskit.__version__, "n_assets": n_assets, "k": k, "reps": reps, "shots": shots, "seed": seed,
               "risk_aversion": risk_aversion, "tickers": tickers,
               "results": [{key: (val.tolist() if isinstance(val, np.ndarray) else val) for key, val in r.items()}
                           for r in results]}
    try:
        from js import sendFile  # Qollab only: offers the JSON in the console
        sendFile("qaoa_benchmark.json", "application/json", json.dumps(summary, default=str))
    except ImportError:
        pass
    return summary
