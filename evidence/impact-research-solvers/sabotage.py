"""Sabotage matrix for impact/tests/test_solvers.py (plan row 5).

Copies impact/ to a disposable directory, applies ONE textual mutation per case
(anchor must match exactly once), runs the solver gate. Every case must go RED;
a GREEN case is a NULL RESULT (the gate cannot see that defect).

    python evidence/impact-research-solvers/sabotage.py <impact dir> <scratch dir>
"""
import shutil, subprocess, sys
from pathlib import Path

SRC, DST = Path(sys.argv[1]), Path(sys.argv[2])
CASES = [
    ('xy mixer sign', 'qc_trade/qaoa.py', 'XXPlusYYGate(2 * betas[layer])', 'XXPlusYYGate(-2 * betas[layer])'),
    ('x mixer angle', 'qc_trade/qaoa.py', "qc.rx(2 * betas[layer], range(n))", "qc.rx(betas[layer], range(n))"),
    ('ising J half', 'qc_trade/qaoa.py', 'J = 0.5 * np.triu(off, 1)', 'J = 0.25 * np.triu(off, 1)'),
    ('penalty too small', 'qc_trade/qaoa.py', 'return max(r, 1e-12)', 'return max(r / 20, 1e-12)'),
    ('dicke angle', 'qc_trade/qaoa.py', 'np.sqrt(j / m)', 'np.sqrt(1 / m)'),
    ('rlt wrong rhs', 'qc_trade/optimizer.py', 'a[1 + 3 * m + v, v] = -(k - 1)', 'a[1 + 3 * m + v, v] = -k'),
    ('anneal delta', 'qc_trade/optimizer.py', 'd[i] + d[j] - 2 * Q[i, j])\n', 'd[i] + d[j] + 2 * Q[i, j])\n'),
    ('greedy delta', 'qc_trade/optimizer.py', '            - 2 * Q[np.ix_(ones, zeros)])', '            + 2 * Q[np.ix_(ones, zeros)])'),
    ('random unseeded', 'qc_trade/optimizer.py', "    rng = np.random.default_rng(seed)\n    n = len(Q)\n    block",
     "    rng = np.random.default_rng()\n    n = len(Q)\n    block"),
    ('exact picks worst', 'qc_trade/optimizer.py', 'i = int(np.argmin(values))', 'i = int(np.argmax(values))'),
    ('qaoa decode ignores energy', 'qc_trade/qaoa.py', 'best = int(valid[np.argmin(true_energy[valid])])', 'best = int(valid[0])'),
    ('qaoa unseeded', 'qc_trade/qaoa.py', 'rng = np.random.default_rng(seed)', 'rng = np.random.default_rng()'),
    ('no statevector refusal', 'qc_trade/scaling.py', "if method in {'qaoa', 'qaoa_xy'} and n > QAOA_RUN_MAX_N:", "if False:"),
    ('O4 old gap compare', 'qc_trade/optimizer.py', "'milp_certified': bool(fit.success and gap <= 1e-8),",
     "'milp_certified': bool(fit.success and fit.mip_gap <= 1e-8 if fit.mip_gap is not None else None <= 1),"),
    ('O1 XY baseline over 2^n', 'qc_trade/qaoa.py', "start_space = (1 << n) if mixer == 'x' else comb(n, k)", "start_space = 1 << n"),
    ('O1 approx ratio unconditioned', 'qc_trade/qaoa.py', "pf = p[feasible] / max(p[feasible].sum(), 1e-300)", "pf = p[feasible]"),
    ('O3 cap diverges', 'qc_trade/benchmark.py', "full_exact(mu,cov,prev,config) if", "full_exact(mu,cov,prev,config,max_cases=150) if"),
    ('O3 solver cap 100', 'qc_trade/optimizer.py', "full_exact_max_cases: int = 2000", "full_exact_max_cases: int = 100"),
]
red = 0
for name, f, old, new in CASES:
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('outputs', '__pycache__', '.pytest_cache'))
    p = DST / f
    s = p.read_text()
    assert s.count(old) == 1, (name, s.count(old))
    p.write_text(s.replace(old, new))
    r = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-x', '-p', 'no:cacheprovider', 'tests/test_solvers.py'],
                       cwd=DST, capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or ['?'])[-1]
    red += r.returncode != 0
    print(f"{'RED   ' if r.returncode else 'GREEN!'} {name:30s} exit={r.returncode} {last}", flush=True)
shutil.rmtree(DST, ignore_errors=True)
print(f'SABOTAGE {red}/{len(CASES)} RED')
sys.exit(0 if red == len(CASES) else 1)
