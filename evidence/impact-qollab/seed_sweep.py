"""Stability across seeds, run locally (CPython, BasicSimulator), not on Qollab.

    cd impact-qollab && /tmp/qollab-qaoa-venv/bin/python ../evidence/impact-qollab/seed_sweep.py
For each (n, k) and seeds 1..10: did each solver's answer equal the optimum, and the QAOA P(optimum) sampled and ideal.
"""
import contextlib
import io
import os
import sys
from math import comb

import numpy as np

sys.path.insert(0, os.getcwd())  # run from impact-qollab/, as Qollab does
import main as project  # noqa: E402

print(f"{'n':>2} {'k':>2} {'solver':<24} {'hit opt':>8} {'P(opt) sampled mean [min,max]':>32} {'P(opt) ideal mean':>18} {'feasible %':>11} {'mean s':>7}")
for n, k in [(6, 2), (6, 3), (8, 4)]:
    rows = {}
    for seed in range(1, 11):
        with contextlib.redirect_stdout(io.StringIO()):
            s = project.main(n_assets=n, k=k, reps=2, shots=1024, seed=seed, risk_aversion=6.0)
        for r in s["results"]:
            rows.setdefault(r["solver"], []).append(r)
    for name, rs in rows.items():
        hit = sum(1 for r in rs if r.get("gap") is not None and abs(r["gap"]) < 1e-12)
        secs = np.mean([r["seconds"] for r in rs])
        if "p_opt_sampled" in rs[0]:
            ps = [r["p_opt_sampled"] for r in rs]
            pi = np.mean([r["p_opt_ideal"] for r in rs])
            fe = 100 * np.mean([r["feasible_frac"] for r in rs])
            print(f"{n:>2} {k:>2} {name:<24} {hit:>5}/10 {np.mean(ps):>18.3f} [{min(ps):.3f},{max(ps):.3f}] {pi:>18.3f} {fe:>10.1f}% {secs:>7.3f}")
        else:
            print(f"{n:>2} {k:>2} {name:<24} {hit:>5}/10 {'-':>32} {'-':>18} {'100.0%':>11} {secs:>7.3f}")
    print(f"{n:>2} {k:>2} {'(random k-subset)':<24} {'':>8} {1 / comb(n, k):>18.3f}")
