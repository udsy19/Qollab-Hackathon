# Track 1 (Quantum Impact): Qollab page metadata, demo-video script, rubric self-check

Drafted 2026-10-10 by agent `impact-deliverables` (read-only; nothing run). Every `<from run>` is filled from the recorded run, never before it. Items marked TO CONFIRM BY OWNER must be confirmed before publishing.

## 1. Page metadata

**Title options** (short, no hype):
1. **Portfolio Selection by QAOA: A Skeptical Benchmark** (recommended; the slug follows the title, so choose once)
2. QAOA vs Classical Solvers for ETF Selection
3. Cardinality-Constrained Portfolio QUBO on QAOA

**Description / About** (218 characters; limit 240; paste into both fields, since it is unknown whether they are the same):

> Pick k of 6 ETFs as a QUBO, solve with QAOA in Qiskit (X and XY mixers), and benchmark against exact, MILP, annealing and greedy solvers on one instance. A reproducible, skeptical test: no quantum advantage is claimed.

**Tags:** `qiskit`, `ionq`, `hackathon`, `quantum-impact`, `qaoa`, `qubo`, `optimization`, `finance`, `portfolio-optimization`, `benchmark`. Use the exact theme label the submission form shows.

**Novelty-floor category:** a technical extension (comparative benchmarking). One frozen portfolio-selection instance runs through two QAOA variants (X-mixer with penalty; cardinality-preserving XY-mixer) and four classical solvers, reporting feasibility, objective, optimality gap and runtime for each. Do not claim "novel application context": QAOA for portfolio selection is well known.

**Prior work and credits** (for the write-up):

> **Prior work and credits.** TO CONFIRM BY OWNER: the classical code in this project (QUBO construction, exact/MILP/annealing/greedy solvers, X-mixer and XY-mixer QAOA as NumPy statevector simulations) comes from QC-TRADE, a prototype written on 2026-10-10 (files dated 05:11–05:39 local), inside the build window that opened on 2026-10-09 at 19:00 ET, with AI-tool assistance. No third-party code or tutorial was forked. New in this project: the Qiskit circuits that run on Qollab's `backend`, a Pyodide-compatible runner, the six-ETF benchmark instance, and this write-up.
>
> The two-stage structure (a discrete selection step followed by a continuous allocation step) is adapted from Shinde, Zhu, Shen and Gao, "A quantum computing approach to beam angle optimization" (arXiv:2504.07844; Medical Physics, 2025). That paper chooses proton-therapy beam angles: binary variables select angles and continuous variables set spot intensities. We borrow only the idea of splitting a binary choice from a continuous one; we do not reproduce its method or results. The paper's "quantum" step was a classical simulation of a QUBO solver, not quantum hardware.
>
> The expected returns and covariance are **synthetic** (generated, not market data), chosen to look like six liquid ETFs (SPY, QQQ, IWM, DIA, TLT, GLD). Nothing here is investment advice, and no result on this page is a market result.
>
> AI tools were used to write code and documentation.

If `mu`/`cov` are later derived from licensed Alpaca data, the synthetic-data sentence must change (redistribution unverified; fit note G3). The page must say the Alpaca code and backtest live in the repo's `impact/` folder and are not part of the Qollab project.

## 2. Demo video script (target 2:30; window 2:00–2:45)

Host on **YouTube** (Unlisted or Public): the only host the page can embed. Record in Chrome, Edge, Brave or Opera (Safari cannot run Qollab), signed out, on the real page. About 370 words of voiceover.

| # | time | on screen | voiceover |
|---|---|---|---|
| 1 | 0:00–0:15 | Project Card top: title, About, tags; scroll to the first heading | "Choosing which assets to hold is a combinatorial problem. This project turns it into a QUBO for six liquid ETFs and asks one honest question: can QAOA on Qiskit match strong classical solvers? We do not claim it can beat them." |
| 2 | 0:15–0:30 | The "synthetic returns and covariance" sentence, then the Prior work header | "The returns and covariance are synthetic, and labelled that way. The discrete-then-continuous structure is adapted from an arXiv paper on beam angle optimisation. We credit it and borrow only that idea." |
| 3 | 0:30–0:50 | Run on Qollab → Select QPU → Run settings → Built-in simulator (24q) → Run | "Anyone can run it without signing in. Press Run on Qollab, keep the default settings, pick the built-in simulator and press Run. No keys, no credits." |
| 4 | 0:50–1:15 | Console: loading, the instance (6 assets, k = <from run>), QUBO size, angle search, each QAOA variant's solution | "The code builds the QUBO, then optimises the QAOA angles locally. Two circuits run: a standard X mixer with a cardinality penalty, and an XY mixer that keeps exactly k assets by construction. Every solver sees the same instance." |
| 5 | 1:15–1:50 | The benchmark table: solver, feasible, objective, gap, runtime; highlight exact (gap 0) and the QAOA rows | "Here is the benchmark. Exact enumeration is the reference. The X mixer returned a feasible portfolio in <from run> percent of shots, with a gap of <from run>. The XY mixer was feasible in <from run> percent of shots, with a gap of <from run>. MILP, annealing and greedy found <from run>, in <from run> milliseconds." |
| 6 | 1:50–2:15 | Run again on an IonQ simulator (only if the dialog shows it free; see notes); the single-job message and the result | "Now the same project on an IonQ simulator with a noise model. Qollab allows exactly one job per run, so the angles were tuned locally and only the final circuit is sent. The noise changes the feasible fraction to <from run>. The solution is <from run>." |
| 7 | 2:15–2:35 | The Verdict and Limitations sections; end on the attribution line | "The verdict: at six assets, classical solvers solve this exactly in milliseconds, and the quantum circuits add overhead. We claim no advantage. What we offer is a reproducible benchmark that a skeptical reader can fork and extend. This effort is supported by Qollab and IonQ." |

Notes:
- Record the built-in simulator run first, uncut. Judges grade that path.
- Segment 6: if the dialog shows "Credits apply", do not press Run (owner rule: free simulators only). Use a free IBM noise-model simulator instead, and say the IonQ run was omitted only if that is true.
- Segment 7's verdict is a hypothesis. Rewrite it from the actual run.
- Edit YouTube's auto-captions (accessibility).
- If over 2:45, cut segment 2 first.

## 3. Rubric self-check

**Novelty & creativity.** Strengths: a like-for-like benchmark of two QAOA mixers against four classical baselines on one frozen instance; the skeptical framing with a fair classical reference; the two-stage idea credited to a real paper from another field. Risk: QAOA portfolio selection is textbook and six assets is small, and a panel may score 0 if it reads as a tutorial. Name the category in a "What's new here" heading.

**Technical execution.** Strengths: runs on the built-in simulator with no sign-in, first try; the same objective in every solver with exact enumeration as ground truth; respects the platform (one-line typed `main`, Qollab's `backend`, one IonQ job, local angle tuning). Risk: a Pyodide failure, especially `scipy.optimize.milp`/HiGHS (unknown in Pyodide). If unavailable, show the row as "not available in the browser" with the reason; never drop it silently.

**Impact potential.** Strengths: a real problem (cardinality-constrained selection is the core of index tracking and portfolio construction); honest reporting of where QAOA stands and what would have to change; a forkable template (tickers, `mu`, `cov`, `k`). Risk: six assets and synthetic data. State impact as a reproducible method to test the claim at larger sizes, and report the scaling bounds actually run.

**Documentation quality.** Strengths: a page that stands without the video; a limitations section; visible hygiene (one paragraph per line, KaTeX for the QUBO, alt text, verbatim attribution, MIT, an Expected Output block the real run reproduced). Risks: the wrong default version showing "no write-up yet" (check signed out after every publish); hard-wrapped Markdown; a wrong prior-work line.

**Best of theme (Quantum Impact).** A classical forecast and risk model feeds a QUBO, then QAOA, then classical continuous allocation: all three on the page. The differentiator is credibility, not performance. Never write "quantum advantage", "speedup" or "outperforms" unless the table shows it.

## Open questions
1. Owner: QC-TRADE provenance (started 2026-10-10? AI tools used?).
2. Owner: does the signed-in Select QPU dialog show IonQ simulators as Free?
3. Owner: the submission form's fields, and the exact theme label.
