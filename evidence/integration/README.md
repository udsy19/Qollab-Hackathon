# evidence/integration — the overseer's independent checks of the Track 1 agents' work

Reader: the owner and anyone reviewing `docs/impact/INTEGRATION_AUDIT.md`. Each file names the commit it checked in its filename.

| file | command (run from inside `impact-qollab/`, Python 3.13 venv, qiskit 2.5.2) | exit |
|---|---|---|
| `verify_qaoa_circuits.py` | the check itself (Dicke state, cost layer, XY cardinality, with a control that must fail) | — |
| `verify_qaoa_circuits.<sha>.txt` | `PYTHONPATH=. python ../evidence/integration/verify_qaoa_circuits.py` | in file |
| `impact-qollab-run.<sha>.txt` | `python -c "from main import main; main()"` | in file |
