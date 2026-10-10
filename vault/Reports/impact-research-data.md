---
type: report
status: current
date: 2026-10-10
updated: 2026-10-10
owner: research-data
tags:
  - impact
  - qc-trade
  - data
---

# Impact: the read-only Alpaca historical-data pipeline (research-data)

## Vault check

- **Read:** [[AGENTS]], [[Research/impact-qc-trade-fit]], [[Design/impact-qc-trade-spec]] (sections 3, 10, 11, 13 in full), `impact/ALPACA_PAPER_RUNBOOK.md`, `impact/README.md`, the existing `impact/qc_trade/{alpaca_paper,data,cli}.py` and both test files. [[Index]]: nothing on data caching, manifests or backoff. [[Plan]]: no row names this work yet (O1 holds the Impact vision).
- **Already known:** the read-only GET allow-list, no-redirect rule, sanitized errors, env-only credentials, paginated CSV download with `.partial` publishing, and the 5-minute rule in `data.aggregate_5min` (all in the import).
- **Reused / extended, not rewritten:** `alpaca_paper._get_json` is still the one Alpaca GET path; it gained explicit 429/5xx backoff and an exact (host, path) allow-list. `data.download_alpaca` now uses the shared paginator `alpaca_paper.iter_bar_pages` instead of its own loop (removed). `data.aggregate_5min` is unchanged and is what builds the cached 5-minute bars. `data.file_sha256` is the one hasher. `where.mjs parquet --branches`: 0 hits anywhere, so the cache is new code (`qc_trade/dataset.py`, `qc_trade/fetch.py`).
- **Stale:** the runbook's pilot section and the `.partial` troubleshooting line described the CSV path; rewritten.

## TL;DR

One owner command, `bash scripts/fetch_real_data.sh full`, checks the paper account, probes SIP and IEX entitlement, downloads 1-minute bars for SPY, QQQ, IWM, DIA, TLT, GLD from 2024-01-01 to the latest permitted session into a SHA-256-pinned Parquet cache, validates every symbol-session against the XNYS calendar, and rebuilds 5-minute bars from complete minutes only. It is read-only, resumable, never switches feed and never substitutes synthetic data. **Nothing in it has been run against the real API**: every result below is mocked HTTP or a dry run.

## What the owner runs

```bash
cd impact
python -m pip install -r requirements.txt
bash scripts/fetch_real_data.sh full --dry-run    # optional; no keys, no network
bash scripts/fetch_real_data.sh full              # or: pilot (from 2026-04-01)
```

It prompts `Rotated Alpaca PAPER API key ID:` and `... secret:` with echo off (or uses exported `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY`). Expected output, all non-secret:

```
Read-only download (full, feed=sip, adjustment=raw). No orders will be sent.
[1/5] paper account authenticated: status=ACTIVE trading_blocked=False  orders submitted: 0
[2/5] feed entitlement at 2026-10-09: sip=allowed iex=allowed; requested feed: sip
[3/5] minute bars: 204 symbol-month partitions -> data/alpaca_full_sip_raw_1min
      SPY 2024-01: <n> bars in <p> page(s)
      ...
[4/5] daily bars for volume cross-check: <n> rows
[5/5] validation: <sessions> sessions, <r> rejected (<x>%), <f> flag(s); 5-minute bars kept for <k> sessions
dataset ready: data/alpaca_full_sip_raw_1min/manifest.json  sha256=<hash>
```

Exit codes: 0 done; 1 data/API failure (message says which month); 2 missing keys or bad arguments; 3 requested feed not entitled (it names the feed that did answer and tells the owner to rerun with `--feed iex` explicitly if acceptable). Rerunning resumes. Afterwards every agent uses `--data data/alpaca_full_sip_raw_1min` (the backtest accepts the directory) or `qc_trade.dataset.load_dataset(...)`; `scripts/run_research.sh full` does this itself.

Dry run (first lines of `evidence/impact-research-data/dry-run-full.txt`, clock 2026-10-10T21:07Z):

```
DRY RUN - no network calls, no credentials read, nothing written.
clock: 2026-10-10T21:07:52.016985+00:00  latest permitted XNYS session: 2026-10-09
window: 2024-01-01 .. 2026-10-09  (UTC 2024-01-01T05:00:00Z .. 2026-10-10T04:00:00Z)
feed: sip (never switched)  adjustment: raw  symbols: SPY,QQQ,IWM,DIA,TLT,GLD
cache: data/alpaca_full_sip_raw_1min
GET https://paper-api.alpaca.markets/v2/account   (paper host only; fields kept: status/blocked flags)
GET https://paper-api.alpaca.markets/v2/clock
GET https://data.alpaca.markets/v2/stocks/bars?symbols=SPY&timeframe=1Min&start=2026-10-09T13:30:00Z&end=2026-10-09T13:40:00Z&feed=sip&limit=5&adjustment=raw   (entitlement probe)
GET https://data.alpaca.markets/v2/stocks/bars?symbols=SPY&timeframe=1Min&start=2026-10-09T13:30:00Z&end=2026-10-09T13:40:00Z&feed=iex&limit=5&adjustment=raw   (entitlement probe)
minute-bar partitions to download: 204  (already cached and verified: 0)
GET https://data.alpaca.markets/v2/stocks/bars?symbols=SPY&timeframe=1Min&start=2024-01-01T05:00:00Z&end=2024-02-01T05:00:00Z&limit=10000&feed=sip&adjustment=raw&sort=asc  (+page_token until exhausted)
...
```

## Manifest format

`data/alpaca_<mode>_<feed>_<adjustment>_1min/manifest.json` (gitignored with the whole cache; `*.parquet` and `*.partial` are also ignored anywhere under `impact/`):

| key | content |
|---|---|
| `schema_version`, `dataset`, `status` | `1`, `alpaca-us-equities-1min`, `incomplete` until the last step, then `complete` |
| `mode`, `source`, `data_host`, `paper_host` | run label and the two official hosts |
| `feed`, `adjustment`, `timeframe`, `symbols` | e.g. `sip`, `raw`, `1Min`, the six ETFs |
| `requested_start`, `latest_permitted_session`, `window_start_utc`, `window_end_utc` | the download window |
| `calendar`, `timezone`, `timestamp_convention` | `XNYS (exchange-calendars)`, `America/New_York`, `UTC bar start` |
| `created_utc`, `run_started_utc`, `run_clock_utc`, `run_finished_utc` | timestamps |
| `code_version`, `software` | git SHA; python, pandas, pyarrow, exchange_calendars versions |
| `paper_account` | `paper_only`, `account_status`, blocked flags, `broker_orders_submitted: 0` (no account number, no balances) |
| `entitlement` | `sip` / `iex`: `allowed`, `empty`, `forbidden` or `error-<status>`, with probe session and symbol |
| `files[]` | per symbol-month: `path`, `rows`, `pages`, `first_utc`, `last_utc`, `sha256`, `request` (the exact query parameters, never a key), `downloaded_utc` |
| `daily_files[]` | same, for the 1Day volume cross-check |
| `bars_5min`, `validation` | path, SHA-256, rows/sessions; rejected count and fraction, half days, flag count |
| `coverage` | per symbol: rows, first and last UTC bar |
| `credentials_recorded` | always `false`; the tests grep every written byte for the dummy key and secret |

## Decisions taken inside the brief

- **Adjustment:** default `raw`, matching the existing data contract (intra-session returns only, end flat daily; raw is what a fill would have been). The other Alpaca modes go to a separate cache directory. Raw prices carry splits, so an open more than 15 % away from the previous close is flagged `overnight_gap` for inspection.
- **Latest permitted date:** the last XNYS session whose close is at least 16 minutes old (Alpaca Basic forbids the latest 15 minutes of SIP); the window ends at the following New York midnight.
- **Partitions:** one file per symbol per New York calendar month, bounded at New York midnight so the UTC boundary follows DST and no session is split.
- **Rejection rule:** a symbol-session is rejected when it has no regular bars or any 5-minute bucket lacks one of its five minutes. That is exactly `aggregate_5min`'s default rule. The pipeline computes it twice, independently (report and reconstruction), and refuses to publish if the two disagree.
- **Volume:** zero-volume minutes counted; minute regular-session volume over the daily bar's volume outside 0.5-1.5 is flagged. The expected ratio on real SIP data is **unknown** (daily bars may include extended hours), so it is a flag, never a rejection.
- **HTTP:** adapter retries are now connection-level only; status retries (429, 500, 502, 503, 504) are explicit in `_get_json`: 6 attempts, 1, 2, 4, 8, 16 s capped at 60 s, `Retry-After` honoured.

## Test results

`cd impact && /tmp/qct-data-venv/bin/python -m pytest -v -p no:cacheprovider tests` → exit 0, **52 passed in 4.00s** (Python 3.12.11, pyarrow 26.0.0, exchange-calendars 4.13.2; venv outside the repo). 28 were pre-existing (baseline: 28 passed before any change), 24 are new in `impact/tests/test_data_pipeline.py`. Log: `evidence/impact-research-data/pytest.txt`.

Sabotage, the gate's own check: `evidence/impact-research-data/sabotage_data.py` applies 18 mutations to a scratch copy (silent feed fallthrough, no backoff, no SHA check on load, secret in the manifest, secret on stdout, fixed 390-minute sessions, incomplete bucket accepted, empty month cached, no gap flag, repeated page token accepted, `/v2/orders` allowed, resume without verification, no volume cross-check, no 16-minute delay, redirects followed, 5m/report consistency check removed, dry run touching the network, dry run writing the cache). **18 of 18 went red** (`evidence/impact-research-data/sabotage.txt`). In the first pass 3 survived (empty month, repeated token, 5m/report consistency) and the feed-fallthrough gate passed for the wrong reason; each got its own gate before this count.

Scale (timing only, synthetic 4,002,480-row frame, never cached): validation 14.6 s, 5-minute reconstruction 27.8 s, peak RSS 2.4 GB (`evidence/impact-research-data/scale-check.txt`).

## What is unverified (needs the real API)

- That the paper keys authenticate, and which feeds this account is entitled to. Nothing here has contacted Alpaca.
- The real payload shape beyond the documented fields (`t, o, h, l, c, v, n, vw`, `next_page_token`); the fake follows the docs, not a captured response.
- Real rate-limit headers (the code honours `Retry-After`; whether Alpaca sends it rather than only `X-RateLimit-Reset` is unchecked), and real wall-clock time for about 600 requests.
- The rejected-session fraction on real SIP minutes. If one ETF misses a single minute, the whole session goes for all six; the backtest's own threshold is 15 %. If real data exceeds it, that is a finding to report, not a threshold to loosen.
- The usual minute-over-daily volume ratio on SIP, and so whether the 0.5-1.5 flag band is too tight.
- Whether any of the six ETFs had a split in 2024-2026 (the gap flag will show it).

## Scope and hand-offs

- Untouched by this change: `optimizer.py`, `benchmark.py` (research-solvers), and `backtest.py`, `audit.py`, `demo.py`, `cli.py` (research-audit). `pyproject.toml` and `requirements.txt` each gained one line, `pyarrow>=15`.
- `cli.py fetch-alpaca` (CSV) still exists and still works through `data.download_alpaca`, which now shares the paginator. Suggestion for research-audit: retire the subcommand in favour of `python -m qc_trade.fetch`, then delete `download_alpaca` in the same change.
- Licensing: the cache is licensed SIP data. It stays under gitignored `impact/data/` and must not be bundled into the Qollab project (gap G3 in [[Research/impact-qc-trade-fit]]).

Code: `impact/qc_trade/fetch.py`, `impact/qc_trade/dataset.py`, `impact/qc_trade/alpaca_paper.py`, `impact/qc_trade/data.py`, `impact/scripts/fetch_real_data.sh`, `impact/scripts/run_research.sh`, `impact/tests/test_data_pipeline.py`, `impact/ALPACA_PAPER_RUNBOOK.md`.
