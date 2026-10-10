# evidence/impact-research-audit — Plan row 4 (agent research-audit)

Reader: `docs/impact/INTEGRATION_AUDIT.md` (§ research-audit), which cites these files. All inputs are synthetic (`impact/qc_trade/demo.py`) or random test instances. Nothing here is market evidence.
Run from `impact/` with the venv `/tmp/qct-venv` (`pip install -r impact/requirements.txt`, Python 3.13.0).

| file | what it shows | how it was produced |
|---|---|---|
| `pytest-before.txt` | `28 passed` on the unmodified import | `python -m pytest -q` |
| `probe_leak.py` → `probe-leak-unmodified.txt` | unmodified engine: perturbing future open/close/volume changes nothing before the cut (no leak) | `PYTHONPATH=. python ../evidence/impact-research-audit/probe_leak.py` |
| `probe_defects.py` → `probe-defects-unmodified.txt` | five defects confirmed on the unmodified tree | `PYTHONPATH=. python ../evidence/impact-research-audit/probe_defects.py` |
| `integrity-red-before-fix.txt` | `15 failed` — new tests on the unfixed tree | `python -m pytest -q tests/test_backtest_integrity.py` at commit `45b6c3b` |
| `pytest-after.txt` | `43 passed` after the fixes | `python -m pytest -q` |
| `demo-run.txt` | synthetic demo regenerated with the new engine + audit (all gates FAIL, as they must on synthetic data) | README section C command + `python -m qc_trade.cli audit --out outputs/demo` |
| `compare_engines.py` | old weight-drift engine (from `main`) vs new ledger, identical settings: agree within 1e-5 in fractional mode | `python compare_engines.py <path-to-old-impact> fractional 100000` (old package via `git archive main impact/qc_trade`) |
| `sabotage.py` → `sabotage-round-1.txt`, `sabotage-round-2.txt` | 12 one-at-a-time mutations on a disposable copy; round 1 exposed S3 NULL and the old test's S1 NULL; round 2 all caught except S2 vs the strictly-before test (by construction) | `python sabotage.py <impact-dir> <scratch-dir>` |
| `measure_audit.py` → `measure_audit.txt` | engine runtime per session; QAOA-vs-uniform-sampling: 256 random shots find the QUBO optimum 20/20 at n=6, k=2 | `PYTHONPATH=. python ../evidence/impact-research-audit/measure_audit.py` |
| `benchmark-full-exact-cap.txt` | `choose('full_exact')` fails at n=10, k=3 while the benchmark reference succeeds (cap 100 vs 150) | inline command in the report |
