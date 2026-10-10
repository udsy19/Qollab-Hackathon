# evidence/impact-research-data

Agent `research-data`, 2026-10-10. Read-only Alpaca historical-data pipeline for `impact/` (QC-TRADE).
No file here touched the network or used a real credential.

| file | produced by | what it shows |
|---|---|---|
| `pytest.txt` | `cd impact && /tmp/qct-data-venv/bin/python -m pytest -v -p no:cacheprovider tests` (Python 3.12.x venv outside the repo) | 82 passed after merging main (2026-10-10): 39 new in `tests/test_data_pipeline.py` (some parametrized) + the rest pre-existing/main's |
| `sabotage.txt` | `python sabotage_data.py <impact> <scratch> <python>` | 25 mutations of the pipeline (S19-S25 = audit findings O5-O7), each re-running the whole suite; all 25 RED |
| `sabotage_data.py` | - | the mutation list (copies `impact/` to a scratch dir; never edits the tree) |
| `dry-run-full.txt`, `dry-run-pilot.txt`, `dry-run-smoke.txt` | `bash impact/scripts/fetch_real_data.sh full|pilot|smoke --dry-run` with no APCA_* variables set, stdin closed | every GET the real run would make; no prompt, no network, nothing written |
| `scale-check.txt`, `scale_check.py` | `python scale_check.py <impact>` | timing of validation + 5-minute reconstruction on a 4.0M-row frame (synthetic, timing only, never cached) |
