# QC-TRADE / Alpaca Paper connection runbook

## Current evidence status

- **Credentials:** paper account key pair supplied by the user, intentionally **not** stored, embedded, uploaded to any plugin, or included in this archive.
- **Paper authentication:** not yet independently checked (this environment cannot resolve Alpaca's hostnames).
- **Historical data ingestion:** fully implemented and tested with paginated mock HTTP fixtures; genuine API data not fetched from this environment.
- **Simulation:** offline trading/solver tests passed. Never treat synthetic NAV/Sharpe as actual trading evidence.
- **Paper orders:** **zero**. The code is deliberately read-only.

## Protect credentials before running

1. Open Alpaca's dashboard for the **paper** account and rotate/revoke the disclosed API pair.
2. Do not send the new pair in chat or copy them into the repository or its README.
3. On your own Mac or Linux machine, run the interactive script. It asks for API ID and secret without printing either.
4. `.gitignore` excludes `.env`, local `data/`, and the real-data experiment folders; use `umask 077` and never publish licensed price data without permission.

## Download the historical data (run once, in your own terminal)

```bash
cd impact
python -m pip install -r requirements.txt          # adds pyarrow for the Parquet cache
bash scripts/fetch_real_data.sh full --dry-run      # optional: every GET it would make; no keys, no network
bash scripts/fetch_real_data.sh full                # prompts for the rotated PAPER key ID and secret, echo off
```

`pilot` instead of `full` downloads from 2026-04-01 only. Options: `--feed sip|iex` (default `sip`), `--adjustment raw|split|dividend|all` (default `raw`). Exported `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY` are used without a prompt. The run:

1. `GET /v2/account`, `GET /v2/clock` on the **paper** host. Success proves the keys are paper keys; only status/blocked flags are kept, never the account number or balances.
2. Probes **both** feeds with a 5-bar SPY request at the latest permitted session and reports `sip=` / `iex=` as `allowed`, `empty`, `forbidden` or `error-<status>`. If the requested feed is not `allowed` it **stops** (exit 3) and names the feed that answered; it never switches feed on its own.
3. Downloads 1-minute bars per symbol per New York calendar month (`GET /v2/stocks/bars`, `limit=10000`, `sort=asc`, following `next_page_token`; HTTP 429/5xx retried with exponential backoff 1, 2, 4, ... s capped at 60 s, honouring `Retry-After`, 6 attempts). Each month is written atomically to Parquet and recorded in the manifest at once, so an interrupted run **resumes**: rerun the same command and SHA-verified months are reused.
4. Downloads 1-day bars per symbol, only to cross-check minute volume.
5. Validates every symbol x XNYS session, writes `validation.json`, rebuilds 5-minute bars with the unchanged `data.aggregate_5min` rule, and refuses to publish if the two disagree.

A month with sessions but zero bars, a repeated page token, an altered cache file or a non-entitled feed is a **failure**, never a skip; nothing synthetic is ever substituted. Latest permitted date: the last XNYS session whose close is at least 16 minutes old (Alpaca Basic forbids the most recent 15 minutes of SIP).

Then `bash scripts/run_research.sh pilot|full` reuses the same cache (`data/alpaca_<mode>_sip_raw_1min/`) and runs the backtest on it: `--data` accepts the cache directory, and the backtest's `data_file_sha256` is the manifest's hash.

### The cache and its manifest (`data/alpaca_<mode>_<feed>_<adjustment>_1min/`, gitignored)

| file | content |
|---|---|
| `minute/<SYM>/<YYYY-MM>.parquet` | raw Alpaca 1Min bars, all hours returned: `timestamp` (UTC bar start), `symbol`, `open`, `high`, `low`, `close`, `volume`, `trade_count`, `vwap` |
| `daily/<SYM>.parquet` | 1Day bars, volume cross-check only |
| `bars_5min.parquet` | `timestamp, symbol, open, close, volume, session` from complete minutes only |
| `validation.json` | per symbol x session: expected minutes, regular bars, missing minutes, incomplete 5m buckets, zero-volume minutes, extended-hours bars, regular/daily volume and ratio; `rejected_sessions`; `flags` |
| `manifest.json` | feed, adjustment, timeframe, symbols, requested start, latest permitted session, UTC window, calendar, code version (git SHA), library versions, paper-account status flags, feed entitlement, and per file: path, rows, pages, first/last UTC, **SHA-256**, the exact request parameters, download time. `credentials_recorded: false` |

Loading (`qc_trade.dataset.load_dataset` or `read_minute_csv(<dir>)`) re-hashes every file against the manifest and raises on any mismatch.

### Adjustment (corporate actions)

Default `adjustment=raw`: tradable prices as printed. The strategy forms returns only **within** a session and ends each day flat, so a split or dividend between sessions does not enter a return; raw prices are also what a fill would have been. `split`/`dividend`/`all` are Alpaca's back-adjusted series and go to a separate cache directory (never mixed). Because raw prices carry splits, `validation.json` flags every open more than 15 % away from the previous regular close (`overnight_gap`) for inspection; nothing is rejected on that flag.

### Calendar, time zone, half days, DST

Sessions come from `exchange-calendars` XNYS (holidays and early closes included); every timestamp is UTC, and the session date is the New York date. Half days are 210-minute sessions (42 five-minute bars). Monthly partitions begin at New York midnight, so the UTC boundary moves with DST (e.g. 2024-03-01T05:00Z, 2024-04-01T04:00Z) and no session is split. Bars on a non-session date are flagged.

### Completeness rule

A symbol-session is **rejected** if it has no regular-hours bars or any 5-minute bucket lacks one of its five 1-minute bars: exactly the rule `aggregate_5min` enforces (default `min_one_minute_bars=5`); one rejected symbol removes that session for all symbols. Flags, not rejections: zero-volume minutes (counted), minute-vs-daily volume ratio outside 0.5-1.5 (`daily_volume_mismatch`), overnight gaps, bars on non-session dates.

## Try the pilot

```bash
bash scripts/run_research.sh pilot
```

This runs the data download above (pilot window), reconstructs 5-minute bars only from complete 1-minute observations, and runs a pilot benchmark with an 2026-08-03 chronological holdout. The runner retains historical feed identity and hashes the download. **A pilot is a connectivity/mechanics test, not conclusive evidence of alpha.**

For the multi-year pre-registered experiment:

```bash
bash scripts/run_research.sh full
```

This downloads from 2024-01-01 through the beginning of the current UTC day, uses the settings predetermined in `EXAMPLE_EXPERIMENT_PLAN.md`, and evaluates 2026 beginning 2026-01-02. It writes `RESEARCH_AUDIT.md`. It is your responsibility to keep 2026 untouched during development; adjusting strategy settings after reading holdout metrics invalidates the locked holdout.

### Alpaca endpoints and access

| Operation | Endpoint | Broker orders? |
|---|---|---|
| Paper account state | `GET https://paper-api.alpaca.markets/v2/account` | No |
| Market clock | `GET https://paper-api.alpaca.markets/v2/clock` | No |
| Old historical SIP probe and download | `GET https://data.alpaca.markets/v2/stocks/bars` | No |

Alpaca Basic generally permits older historical SIP bars, while current real-time equities on the free plan are IEX only; historical consolidated SIP has a restriction on the most recent 15 minutes. The system uses only old historical SIP for research. Documentation: https://docs.alpaca.markets/us/docs/about-market-data-api and https://docs.alpaca.markets/us/docs/historical-api . Verify current license and subscription in the dashboard.

### Connection troubleshooting

- `401`: keys expired, revoked, pasted incorrectly, or do not belong to the paper account. Rotate and rerun locally.
- `403`: the requested SIP historical feed may not be allowed. Check entitlement, time boundaries and then optionally test `--feed iex` on a smaller research sample; do not substitute feeds silently.
- `429`: API call limit reached. The historical downloader has retries and backoff on rate-limited responses.
- `Could not connect`: local firewall/DNS/VPN/internet, no network access here. Do not assume that means the key was invalid.
- Too many incomplete sessions: consolidated volume may be incomplete for one of the tickers or earlier market data not retrieved. Inspect rejected dates; don't lower coverage thresholds just to obtain better returns.
- `.partial` file or `"status": "incomplete"` in the manifest: the download stopped. Rerun the same `fetch_real_data.sh` command; SHA-verified months are reused. The full run is roughly 204 symbol-months (about 4M minute rows); validation and 5-minute reconstruction take about 45 s and 2.4 GB RAM on a laptop (`evidence/impact-research-data/scale-check.txt`).
- Exit 3 `Requested feed 'sip' is forbidden`: your plan does not permit SIP at that date. Decide explicitly whether `--feed iex` (one exchange, sparser minutes, more rejected sessions) is acceptable; it is never chosen for you.

### What must happen before paper order routing

1. Verify positive *locked* out-of-sample net results versus classical **allocation and trading** baselines. This may fail, and failure is an important finding.
2. Add quote/NBBO execution simulation and measure IEX versus SIP discrepancies; historical OHLCV cannot give actual fills.
3. Run paper trading with explicit opt-in; enforce market-hours only, intraday flatting, kill switch, maximum order notional, position caps, idempotent client order IDs, and paper-order/position reconciliation.
4. After a meaningful paper-forward sample, compare predicted fills with actual paper fills, evaluate economic risk, and never infer real-money profits from paper fills alone.

**No live-money trading or paper order placement is authorized or built into this version.**
