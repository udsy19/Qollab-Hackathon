---
type: design
status: current
date: 2026-10-10
updated: 2026-10-10
owner: owner
tags:
  - impact
  - qc-trade
---

# Impact track — the owner's QC-TRADE spec (verbatim)

Given by the owner on 2026-10-10 16:44 ET as the product vision for Track 1, Quantum Impact. It is reproduced as given; agents do not edit it. How it is cut to fit the hackathon deadline and Qollab is recorded separately, in [[Vision]] and the [[Plan]], never here. The project's fit to Qollab is [[Research/impact-qc-trade-fit]]. Source paper: https://arxiv.org/pdf/2504.07844

---

# Claude Code Prompt: QC-TRADE — Quantum-Enhanced Intraday Trading System

You are a senior quantitative researcher, quantum computing scientist, algorithmic trading engineer, and production-grade Python developer.

Your task is to take my existing **QC-TRADE** project and transform it into a fully functional, rigorously benchmarked intraday trading research platform for US stocks and ETFs, integrated with my Alpaca paper-trading account.

**Do not simply propose an architecture or write a research plan. Implement the system, execute available tests, debug problems, run experiments using real historical data where accessible, and produce reproducible results.**

## 1. Project Background

QC-TRADE is inspired by this research paper:

https://arxiv.org/pdf/2504.07844

The paper presents a hybrid quantum-inspired approach to optimization, combining binary selection with continuous optimization.

We are adapting that structure to financial markets:

- Binary optimization decides which securities to hold.
- Continuous optimization determines portfolio allocation.
- Predictive models estimate intraday returns.
- A realistic execution simulator estimates achievable profitability.
- Quantum and classical solvers compete on identical optimization instances.

My objective is twofold:

1. Achieve statistically credible, out-of-sample trading profitability after realistic costs.
2. Investigate whether quantum or quantum-inspired optimization delivers measurable computational or solution-quality advantages over strong classical optimization.

These are independent objectives. Do not conflate them.

The original paper's quantum-inspired results do not establish a quantum hardware speedup. Do not claim one without supporting evidence.

## 2. First: Audit the Existing Codebase

Before making modifications:

1. Read the entire repository, README, Alpaca runbook, experiment plan, and validation checklist.
2. Understand the existing market-data layer, optimizers, backtesting logic, benchmark suite, and tests.
3. Run all existing automated tests.
4. Identify incomplete functionality, incorrect assumptions, data leakage, unrealistic execution modeling, mathematical errors, and performance bottlenecks.
5. Produce a concise audit of what works, what is broken, and what needs improvement.

Preserve useful existing functionality. Refactor or replace weak implementations when justified.

Do not rewrite everything unnecessarily.

## 3. Alpaca Integration and Real Market Data

Use Alpaca's official APIs.

Paper trading endpoint:
https://paper-api.alpaca.markets/v2

Historical market-data endpoint:
https://data.alpaca.markets/v2

Credentials must come from environment variables or a secure local prompt.

Never hardcode credentials, print secrets, commit them to Git, or include them in generated reports.

Assume that any credentials previously shared through chat have been exposed and must be rotated.

Implement:

- Paper-account connectivity verification.
- Historical stock and ETF bar downloading.
- SIP-versus-IEX feed detection and entitlement checks.
- Cursor-based historical data pagination.
- Rate-limit handling, retries, and exponential backoff.
- Local Parquet caching with dataset provenance.
- Adjusted-price/corporate-action handling.
- NYSE market calendars and timezone handling.
- Half-day sessions, holidays, and daylight-saving transitions.
- Data completeness checks, missing-bar detection, and volume validation.
- Reproducible historical dataset manifests.

Never substitute synthetic data when historical downloads fail.

Begin with a liquid ETF universe: SPY, QQQ, IWM, DIA, TLT, and GLD.

Expand to other liquid ETFs and US stocks only after establishing a stable baseline. Avoid survivorship bias when evaluating historical stock universes.

Build the dataset from January 2024 through the latest historical date permitted by the account.

Use chronological training, validation, and untouched holdout windows. The current research target is a 2026 out-of-sample evaluation, with all decisions restricted to information available at each point in time.

## 4. Intraday Trading Strategy

Start with these defaults:

- One-minute source data.
- Five-minute feature bars.
- Decisions every 30 minutes.
- Long-only portfolio.
- No leverage.
- Maximum 2–3 open positions.
- Configurable maximum position concentration.
- No overnight positions.
- Forced liquidation before session close.
- Conservative initial capital assumption of $25,000.
- All parameters configurable.

Implement several predictive models:

1. Momentum and mean reversion.
2. Volatility-adjusted momentum.
3. Ridge/elastic-net regression.
4. Gradient-boosted trees.
5. Optional more complex models only when justified by evidence.

Use strictly causal features including historical returns, rolling volatility, volume anomalies, relative strength, intraday seasonality, VWAP deviation, and cross-asset correlations.

Predictions must target a precisely defined future holding period.

Prevent look-ahead bias, target leakage, inappropriate full-sample normalization, overlapping-label contamination, and train/test contamination.

Use chronological walk-forward training with validation and suitable embargoes where necessary.

Record forecast quality separately from trading performance.

## 5. Quantum and Classical Portfolio Optimization

Preserve the paper's central hybrid idea:

**Stage A: Discrete asset selection.**

Formulate a QUBO that considers expected returns, covariance, diversification, turnover, concentration, and cardinality constraints.

**Stage B: Continuous allocation.**

Given selected assets, optimize allocation using a constrained classical solver.

Implement and benchmark:

- Exact enumeration for sufficiently small problems.
- Strong mixed-integer optimization using HiGHS or another appropriate solver.
- Classical simulated annealing.
- Greedy/local search with improvements.
- Standard QAOA simulation.
- Cardinality-preserving XY-mixer QAOA.
- Additional quantum-inspired approaches only if they offer a credible advantage.

Ensure all solvers optimize equivalent mathematical objectives under equivalent constraints.

When a formulation differs, document and justify the difference.

Report feasibility, objective value, optimality gap or best-known gap, runtime, memory consumption, and stability across random seeds.

Measure both:

1. Discrete QUBO optimization quality.
2. Full portfolio objective quality after continuous allocation.

Critically, benchmark **end-to-end computational time**, including problem construction, solver initialization, optimization, solution decoding, continuous refinement, and any compilation or communication overhead.

Distinguish classical statevector simulation from execution on real quantum hardware.

Do not advertise simulated QAOA results as real quantum speedups.

## 6. Realistic Backtesting and Execution

This is one of the most important requirements.

Build an event-driven backtesting engine that simulates exactly when information becomes available and when an order could execute.

Account for:

- Next-bar execution latency.
- Bid-ask spread.
- Slippage.
- Commissions and applicable fees.
- Market impact approximations.
- Liquidity and participation constraints.
- Position-size limits.
- Partial fills or conservative fill assumptions.
- Volume limitations.
- Trading halts and missing market data.
- Market opening and closing behavior.
- Portfolio cash accounting.
- End-of-day liquidation costs.

Never execute at the same bar's price if the signal depends on that bar's closing information.

With OHLCV-only data, explicitly label spread, impact, and fill assumptions as modeled rather than observed. Incorporate quote data if actually available.

Use multiple execution-cost scenarios:

- Optimistic.
- Base case.
- Conservative.
- Severe stress.

Calculate portfolio equity from actual simulated holdings, cash, and fills rather than adding predicted returns directly.

Add tests that deliberately modify future prices and verify past trading decisions do not change.

## 7. Classical Trading Baselines

Compare QC-TRADE against:

- Cash.
- Buy-and-hold SPY.
- Equal-weight portfolio.
- Top-K momentum.
- Minimum-variance portfolio.
- Classical mean-variance optimization.
- Classical mixed-integer portfolio optimization.
- Simple intraday momentum and mean-reversion strategies.

Ensure benchmarks operate over identical sessions with comparable capital, execution timing, and costs.

Do not compare an intraday strategy that exits every day against an overnight SPY position without explicitly separating the different exposure profiles.

Also evaluate whether replacing QC-TRADE's discrete optimizer with a strong classical optimizer improves or worsens trading outcomes.

This ablation is essential.

## 8. Out-of-Sample Profitability Evaluation

Generate the following metrics:

- Total net return.
- Annualized return, where meaningful.
- Annualized volatility.
- Sharpe ratio.
- Sortino ratio.
- Maximum drawdown.
- Calmar ratio.
- Win rate.
- Profit factor.
- Average trade P&L.
- Turnover.
- Exposure-adjusted return.
- Transaction-cost drag.
- Daily and monthly P&L.
- Number of trading days and trades.

Include uncertainty estimates using suitable block-bootstrap methods and paired daily-return comparisons.

Account for multiple testing and strategy selection bias.

Do not select winning strategies using the final holdout.

Include parameter sensitivity analysis and regime breakdowns for high volatility, low volatility, trending, and range-bound markets.

A strategy that is profitable only under optimistic execution assumptions must not be classified as validated.

Distinguish statistical significance from economically meaningful net returns.

## 9. Computational Scaling Research

I want to know whether the quantum approach can become meaningfully superior to classical optimization.

Generate optimization instances with increasing problem sizes, for example:

N = 6, 10, 15, 20, 30, 50, and 100 assets, subject to practical resource limits.

For each size, benchmark:

- Solver objective.
- Feasible solution rate.
- Optimality gap where verifiable.
- End-to-end runtime.
- Peak memory.
- Variance across seeds.
- Time-to-target solution quality.

Respect simulation feasibility. Do not attempt large QAOA statevector simulations that exceed practical memory limits.

Record explicitly which configurations could not be completed and why.

Plot scaling curves and describe the implications honestly.

If classical optimization wins, document that result.

My priority is scientific credibility, not manufacturing evidence of quantum advantage.

Also investigate whether the research would be more promising for optimal execution scheduling, portfolio construction, or another financial optimization problem.

Do not change the primary research question without documenting the reasoning.

## 10. Reproducibility and Software Engineering

Use Python and maintain a clean modular codebase.

Prefer established libraries such as:

- NumPy and pandas.
- SciPy and HiGHS.
- scikit-learn.
- Qiskit or another justified quantum simulation framework.
- PyArrow/Parquet.
- pytest.
- Matplotlib or Plotly.

Avoid unnecessary dependencies.

Implement:

- Strict configuration files.
- Deterministic random seeds.
- Structured logging.
- Data and experiment provenance.
- Versioned experiment outputs.
- Unit and integration tests.
- Continuous integration where practical.
- Explicit error reporting.
- Checkpointing for long benchmark runs.

Protect the system against incomplete data and silently failed optimizations.

Use CPU parallelism responsibly.

No GPU or quantum hardware should be assumed unless detected and explicitly configured.

## 11. Paper-Trading Safety

The account is a paper account, not a live-money account.

For this phase, **do not submit any orders**, even simulated paper orders.

You may implement a read-only account adapter and a dry-run execution preview.

Any future paper-order submission must require separate explicit authorization and a clearly enabled execution mode.

Never connect to a live-money endpoint or silently fall back to live trading.

## 12. Required Deliverables

Produce:

1. A working, updated QC-TRADE codebase.
2. A verified historical-data acquisition pipeline.
3. A runnable, walk-forward intraday backtest.
4. A reproducible quantum-versus-classical benchmark suite.
5. Trading-performance and computational-performance comparison reports.
6. Equity curves, drawdown plots, solver-scaling charts, and cost-sensitivity charts.
7. A research audit explaining limitations and possible biases.
8. Updated README and operating instructions.
9. Automated tests and their actual results.
10. A prioritized roadmap toward a properly controlled paper-trading experiment.

Generate a final report named `RESEARCH_RESULTS.md`.

The report must state clearly:

- What was implemented.
- What was actually executed.
- Which data sources were used.
- Which experiments passed or failed.
- Whether the strategy generated positive net out-of-sample returns.
- Whether it beat appropriate classical trading baselines.
- Whether quantum-inspired optimization beat classical optimization.
- What remains unverified.
- Whether the system is ready for paper trading.

Never invent numerical results or report synthetic experiments as real market results.

## 13. Execution Instructions

Work autonomously through the repository.

1. Audit the current implementation.
2. Fix correctness issues first.
3. Establish reliable historical market-data access.
4. Build a trustworthy classical baseline.
5. Run the real-data backtest where access permits.
6. Evaluate quantum and quantum-inspired optimization.
7. Compare all approaches fairly.
8. Generate reproducible reports.
9. Run the full test suite and address failures.
10. Report the actual findings.

If Alpaca credentials are unavailable, ask for them through a secure local input mechanism or use existing environment variables. Do not request that secrets be pasted into chat.

If external access fails, provide a reproducible command for the blocked experiment and continue with all independently testable work.

Do not claim completion of any experiment that was not run.

Do not stop after creating a plan. Implement, test, validate, and document as much of the system as the environment permits.

**Final research principle:** Our goal is not to prove that quantum computing is better. Our goal is to discover whether it genuinely offers an advantage in a financially meaningful optimization problem, using rigorous measurements that a skeptical quantitative researcher could reproduce.
