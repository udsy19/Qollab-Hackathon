"""Apply one sabotage at a time to impact-qollab/, run scripts/gates/impact-qollab-run.py, restore the file byte for byte.

    /tmp/qollab-qaoa-venv/bin/python evidence/impact-qollab/sabotage.py
Every case must make the gate exit 1. A case that leaves it at 0 is a null result: the gate cannot see that fault.
"""
import os
import subprocess
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PY = sys.executable
CASES = [
    ("second job: one run() per circuit", "impact-qollab/main.py", 'job_result = backend.run(compiled, shots=shots, **run_options).result()',
     'job_result = backend.run(compiled[:1], shots=shots).result(); backend.run(compiled[1:], shots=shots)'),
    ("Dicke angle off", "impact-qollab/qctrade/qaoa.py", 'acos(sqrt(1 / m))', 'acos(sqrt(1 / (m + 1)))'),
    ("Ising J doubled", "impact-qollab/qctrade/qaoa.py", 'J = np.triu(S, 1) / 2', 'J = np.triu(S, 1)'),
    ("exact solver picks the worst", "impact-qollab/qctrade/solvers.py", 'best = min(combinations', 'best = max(combinations'),
    ("SYNTHETIC warning dropped", "impact-qollab/main.py", 'These numbers are SYNTHETIC.', 'These numbers are illustrative.'),
    ("gap misreported", "impact-qollab/main.py", 'r["gap"] = r["energy"] - e_opt', 'r["gap"] = abs(r["energy"] - e_opt) * 0.5'),
    ("XY mixer replaced by RX (breaks feasibility)", "impact-qollab/qctrade/qaoa.py",
     'qc.append(XXPlusYYGate(2 * float(beta)), [i, j])', 'qc.rx(2 * float(beta), i)'),
]
missed = 0
for label, f, a, b in CASES:
    p = os.path.join(W, f)
    orig = open(p).read()
    assert a in orig, (label, a)
    try:
        open(p, "w").write(orig.replace(a, b, 1))
        r = subprocess.run([PY, os.path.join(W, "scripts/gates/impact-qollab-run.py")], capture_output=True, text=True)
        fails = [l.strip() for l in r.stdout.splitlines() if l.strip().startswith("FAIL")]
        last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]
        missed += r.returncode != 1
        print(f"SABOTAGE [{label}] -> exit {r.returncode}; {len(fails)} FAIL; first: {fails[0] if fails else '-'}; {last}")
    finally:
        open(p, "w").write(orig)
print(f"SABOTAGE SUMMARY: {len(CASES) - missed} of {len(CASES)} caught")
sys.exit(1 if missed else 0)
