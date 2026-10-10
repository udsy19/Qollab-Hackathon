# Pre-registration — first real-data QC-TRADE backtest (2026-10-10)

Committed BEFORE any backtest on real data was run. No 2026 (or any) return on real data has been seen by anyone when this was written. Follows `impact/EXAMPLE_EXPERIMENT_PLAN.md`; deviations are listed and justified by data quality only.

## Data (frozen)
- `impact/data/alpaca_full_sip_raw_1min/` (gitignored, licensed; not redistributed). Manifest SHA-256 `c579b58d70a646aed7abdf37e4615b4772483e36c6e63b427dab04d3e856f892`.
- Alpaca SIP 1-minute bars, raw (unadjusted), 2024-01-01..2026-10-09, SPY QQQ IWM DIA TLT GLD; 3,010,839 minute rows; 696 sessions; 0 orders.
- Pipeline validation: 280 of 696 sessions rejected (DIA 262, GLD 32, TLT 5); rejected TLT sessions are more volatile (p<0.05), so the kept sample is biased toward calmer TLT days. This is disclosed in every result.

## Windows (frozen, from the experiment plan)
Development 2024; validation 2025; locked out-of-sample **2026-01-02..2026-10-09** (`--test-start 2026-01-02`).

## Analyses
1. **Primary (as pre-registered):** universe SPY,QQQ,IWM,DIA,TLT,GLD; all other settings = the shipped CLI defaults at this commit (k=2, 30-minute rebalance, 2-bar execution lag, $25,000, whole shares, spread 1.0 / slippage 1.5 / commission 0.2 / impact 1.0 bps, max participation 2%, `--min-minute-bars 5`, `--max-missing-fraction 0.15`); methods `anneal,milp_qubo,exact_qubo,greedy,topk,minvar,spy,equal,cash`; `--stress` (extra 0, 1.5, 5, 10 bps per side and the four named cost scenarios).
2. **Sensitivity (data quality only):** identical, but universe SPY,QQQ,IWM,TLT,GLD (DIA removed because it causes 262 of the 280 rejections). Chosen before any return was seen.

Commands (from `impact/`):
```
python -m qc_trade.cli backtest --data data/alpaca_full_sip_raw_1min --test-start 2026-01-02 --stress --out outputs/real_full_primary
python -m qc_trade.cli backtest --data data/alpaca_full_sip_raw_1min --test-start 2026-01-02 --stress --symbols SPY,QQQ,IWM,TLT,GLD --out outputs/real_full_noDIA
```

## Decision rule (frozen)
A trading claim needs, under the CONSERVATIVE cost scenario, a positive net 2026 return AND a higher net return than the session-flat SPY baseline AND a paired block-bootstrap 95% lower bound above zero. Anything less is reported as not validated. No parameter is changed after the results are seen; any later variant is labelled exploratory. QAOA is not in the backtest methods (the solver comparison is separate); a quantum-vs-classical trading ablation would compare `milp_qubo` with the QAOA methods on identical inputs.
