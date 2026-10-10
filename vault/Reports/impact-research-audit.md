---
type: report
status: current
date: 2026-10-10
updated: 2026-10-10
owner: research-audit
tags:
  - impact
  - qc-trade
---

# Impact — QC-TRADE audit and backtest correctness fixes (Plan row 4)

## Vault check

- **Read:** [[AGENTS]], [[Design/impact-qc-trade-spec]] (sections 2 and 6 are this row's brief), [[Research/impact-qc-trade-fit]], [[Plan]] row 4, [[Sessions/2026-10-10-impact-track-1]], [[Index]].
- **Already known:** the fit note says the README's evidence audit "fails every gate on its synthetic demo", and that QAOA is a NumPy statevector simulation. Both are confirmed here.
- **Reused:** the existing forecast, signal timing, bootstrap, data layer and audit report structure. No prior audit of `impact/` existed in [[Index]], and `where.mjs --branches` found no ledger, cost scenarios or contiguity check anywhere.
- **Stale:** `impact/README.md` on default capital, the `--stress` outputs and accounting (see `impact/AUDIT.md` N7). Plan row 4's gate assumes the perturbation test would be "red before the fix". The property already held, so see "Finding that changes the row's premise".

## TL;DR

- The engine had **no look-ahead leak**. On the unmodified tree, randomly perturbing all future prices and volumes changed nothing before the cut, for every classical method.
- It **did** fail spec §6 in four other ways, all now fixed test-first:
  - equity was not built from holdings, cash and fills;
  - the cost-stress grid replaced slippage when it was documented as adding to it;
  - there were no named cost scenarios;
  - the audit could validate a strategy that was profitable only under optimistic costs.
- The **biggest open issue is outside this row**. The benchmark's "QAOA reaches the exact optimum" result is guaranteed by shot sampling: 256 uniform random samples also find the optimum 20 times out of 20 at the benchmark's size. It says nothing about the quantum circuit (owner: research-solvers).

## Test results

| tree | result | artifact |
|---|---|---|
| unmodified import | `28 passed in 12.68s` | `evidence/impact-research-audit/pytest-before.txt` |
| new integrity tests, unfixed tree | `15 failed in 4.29s` | `evidence/impact-research-audit/integrity-red-before-fix.txt` |
| after the fixes | `43 passed in 8.17s` | `evidence/impact-research-audit/pytest-after.txt` |

## Defects fixed (in `impact/qc_trade/backtest.py`, `audit.py`, `cli.py`, `demo.py`)

1. **Share/cash ledger** replaces weight-drift NAV. Fills happen at the bar open, sells before buys, and buys are capped to the cash on hand. Shares are whole by default. Equity is `cash + shares × close`. The fill and decision logs are written out. In fractional mode the ledger agrees with the old engine to within 1e-5, so the old arithmetic was right and only its representation was missing.
2. **`--stress` is now additive.** It was `replace(slippage_bps=x)`, so the "+0" row was cheaper than the headline run (fees 830 vs 1574).
3. **Four cost scenarios** (optimistic, base, conservative, severe stress), all labelled MODELED, never observed.
4. **New audit gate:** the strategy must make a positive net return under conservative costs. A missing scenario table now fails the audit instead of being skipped.
5. **Panel contiguity guard:** each session must match the XNYS 5-minute grid exactly.
6. **Default capital is $25k**, per spec §4.
7. **`synthetic_panel` works for more than 6 symbols.**
8. **The old future-perturbation test** missed a one-bar look-ahead (sabotage S1). It is replaced by the owner-required test, plus a bar-open variant.

Each defect's file:line, evidence and test: `impact/AUDIT.md`.

## Defects open (other agents' files; proposed fixes in `impact/AUDIT.md`)

- **O1** (research-solvers): the QAOA benchmark's success comes from shot sampling (`optimizer.py:198-202`, `:255-256`). Fix: report the probability mass on the optimum and the approximation ratio, and add a random-sampler baseline.
- **O2** (research-solvers): the X-mixer penalty dominates the standardised energies. The feasible mass is 0.545, which handicaps X against XY.
- **O3** (research-solvers): the `full_exact` cap is 150 in `benchmark.py:58` but 100 by default in `optimizer.py:297`, so n=10, k=3 is recorded as infeasible when it is not.
- **O4** (research-solvers): `mip_gap=None` crashes `optimizer.py:102`.
- **O5–O7** (research-data):
  - O5: the timezone is inferred from the first row only;
  - O6: dropping a whole session for one missing bucket biases the sample towards calm days;
  - O7: running out of retries is misreported as a DNS failure.

## Finding that changes the row's premise

Plan row 4's gate asks for the future-price-perturbation test to be "red before the fix". The causality property already held on the unmodified engine (`evidence/impact-research-audit/probe-leak-unmodified.txt`). The new test was red on the unfixed tree only because `decisions` and `fills` did not exist yet. Its ability to fail is shown by sabotage instead:

- S1, a forecast that peeks one bar ahead: caught.
- S2, a fill that reads its own bar's volume: caught by the bar-open variant.
- S11, the test's own perturbation replaced by the identity: caught.

Round 2 (`evidence/impact-research-audit/sabotage-round-2.txt`) caught 12 of 12 mutations. The one green result, S2 against the strictly-before comparison, is green by construction.

## Evidence

All under `evidence/impact-research-audit/` (index: its `README.md`). The audit itself: `impact/AUDIT.md`. Regenerated synthetic demo: `impact/outputs/demo/`. Every gate fails there, as it must on synthetic data.
