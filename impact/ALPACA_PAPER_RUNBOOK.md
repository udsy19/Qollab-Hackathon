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

## Try the pilot

```bash
python -m pip install -r requirements.txt
bash scripts/run_research.sh pilot
```

This verifies three **read-only** API calls, downloads consolidated SIP 1-minute OHLCV for six ETFs, reconstructs 5-minute bars only from complete 1-minute observations, and runs a pilot benchmark with an 2026-08-03 chronological holdout. The runner retains historical feed identity and hashes the download. **A pilot is a connectivity/mechanics test, not conclusive evidence of alpha.**

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
- `.partial` file exists: incomplete download. `fetch-alpaca` only publishes the target CSV after receiving the final page; rerun to restart it. A full multi-year download may involve substantial data.

### What must happen before paper order routing

1. Verify positive *locked* out-of-sample net results versus classical **allocation and trading** baselines. This may fail, and failure is an important finding.
2. Add quote/NBBO execution simulation and measure IEX versus SIP discrepancies; historical OHLCV cannot give actual fills.
3. Run paper trading with explicit opt-in; enforce market-hours only, intraday flatting, kill switch, maximum order notional, position caps, idempotent client order IDs, and paper-order/position reconciliation.
4. After a meaningful paper-forward sample, compare predicted fills with actual paper fills, evaluate economic risk, and never infer real-money profits from paper fills alone.

**No live-money trading or paper order placement is authorized or built into this version.**
