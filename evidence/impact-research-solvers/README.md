# evidence/impact-research-solvers — plan row 5

Agent `research-solvers`, 2026-10-10. Venv outside the repo: `python3.12 -m venv /tmp/qct-solvers-venv && pip install -r impact/requirements.txt`.

| file | command | exit | result |
|---|---|---|---|
| `pytest.log` | `cd impact && python -m pytest -q` | 0 | `82 passed` (28 pre-existing + 54 in `tests/test_solvers.py`) |
| `sabotage.py`, `sabotage.log` | `python evidence/impact-research-solvers/sabotage.py impact <scratch>` | 0 | `SABOTAGE 18/18 RED` (one mutation per case on a disposable copy) |

The scaling study's own artifacts are in `impact/outputs/scaling/` (`manifest.json`, `trials.jsonl`, `summary.csv`, `not_run.csv`, `milp_probe.csv`, three PNGs). Reproduce them with `cd impact && python -m qc_trade.scaling --out outputs/scaling --workers 3` (about 35 min on 3 single-threaded workers; the checkpoint lets a rerun resume), then `--milp-probe` (about 6 min).

The report is `vault/Reports/impact-research-solvers.md`.
