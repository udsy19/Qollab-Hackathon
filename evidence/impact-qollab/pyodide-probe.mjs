// Probe what of impact-qollab/ runs under Pyodide 314.x (Python 3.14) in Node, outside Qollab.
//   node evidence/impact-qollab/pyodide-probe.mjs <path to node_modules/pyodide> <path to impact-qollab>
// It loads numpy + scipy from the Pyodide distribution, mounts the project read-only into the in-memory FS,
// runs the classical half (instance, QUBO, exact, MILP/HiGHS, greedy, annealing, SLSQP sizing), then tries
// `micropip.install("qiskit>=2.5.2,<3.0.0")` from PyPI. It never touches a Qollab backend. Exit 0 = probe ran to the end.
import fs from 'node:fs'
import path from 'node:path'

const [pyodideDir, projectDir] = process.argv.slice(2)
if (!pyodideDir || !projectDir) { console.log('usage: pyodide-probe.mjs <pyodide dir> <impact-qollab dir>'); process.exit(2) }
const { loadPyodide } = await import(path.join(path.resolve(pyodideDir), 'pyodide.mjs'))
const py = await loadPyodide({ indexURL: path.resolve(pyodideDir) + '/' })
console.log('PYODIDE', py.version, '| python', py.runPython('import sys; sys.version.split()[0]'))

// copy the project's Python and data files into /project
const walk = (d, rel = '') => fs.readdirSync(path.join(d, rel), { withFileTypes: true }).flatMap((e) =>
  e.isDirectory() ? walk(d, path.join(rel, e.name)) : [path.join(rel, e.name)])
for (const f of walk(projectDir)) {
  if (!/\.(py|json)$/.test(f)) continue
  const dst = '/project/' + f
  py.FS.mkdirTree(path.posix.dirname(dst))
  py.FS.writeFile(dst, fs.readFileSync(path.join(projectDir, f)))
}
await py.loadPackage(['numpy', 'scipy', 'micropip'])
console.log(py.runPython(`
import os, sys, time
os.chdir('/project'); sys.path.insert(0, '/project')
import numpy as np, scipy
from qctrade.instance import load_stats, select_universe
from qctrade.solvers import OptConfig, qubo_matrix, exact_qubo, milp_qubo, greedy_swap, anneal_qubo, refine, qubo_energy
out = [f"numpy {np.__version__} scipy {scipy.__version__}"]
stats, origin = load_stats("data/etf_stats_synthetic.json")
tickers, mu, cov = select_universe(stats, 6)
cfg = OptConfig(k=2)
Q = qubo_matrix(mu, cov, np.zeros(6), cfg)
out.append(f"stats from {origin}: {tickers}")
for name, fn in [("exact", lambda: exact_qubo(Q, 2)), ("milp", lambda: milp_qubo(Q, 2)), ("greedy", lambda: greedy_swap(Q, 2)),
                 ("anneal", lambda: anneal_qubo(Q, 2, 300, 4, 7))]:
    t = time.perf_counter()
    try:
        r = fn(); sel = r[0] if isinstance(r, tuple) else r
        w = refine(sel, mu, cov, np.zeros(6), cfg)
        out.append(f"  {name:7s} OK  sel={[tickers[i] for i in sel]} E={qubo_energy(Q, sel):.6f} "
                   f"{(time.perf_counter()-t)*1e3:.1f} ms  extra={r[1] if isinstance(r, tuple) else ''}")
    except Exception as e:
        out.append(f"  {name:7s} FAILED {type(e).__name__}: {e}")
"\\n".join(out)
`))
try {
  await py.runPythonAsync(`import micropip\nawait micropip.install("qiskit>=2.5.2,<3.0.0")`)
  console.log('micropip.install("qiskit>=2.5.2,<3.0.0"): OK')
  console.log(py.runPython('import qiskit; qiskit.__version__'))
} catch (e) {
  console.log('micropip.install("qiskit>=2.5.2,<3.0.0"): FAILED: ' + String(e.message || e).split('\n').filter((l) => /Error|Can't|No |wheel/.test(l)).slice(-3).join(' | '))
}
console.log('PYODIDE-PROBE DONE')
