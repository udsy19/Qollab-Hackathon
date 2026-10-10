=== PLAN ===
**Lane goal:** Produce everything the judges read, for both projects (Playground and Unlocked):
- an MIT LICENSE;
- a README, which on Qollab becomes the project's write-up;
- a Qollab project-page draft covering what it does, the quantum idea, how to run it on Qollab (free simulators including IonQ), and disclosure of prior and third-party code;
- a 2–3 minute demo-video script and shot list the owner can record.

Documentation quality is a judged trait; we aim for the best in the hackathon. We write only in `docs/`, the READMEs and the LICENSEs. The owner publishes to Qollab and posts the video.

**Where things stand (consult 2, 2026-10-10 00:57 UTC, about 20:57 ET Oct 9):**
- `qollab-page-research` is done. I judged it from the report, the note and the screenshots, and it passes. The note is `vault/Research/qollab-platform-and-submission.md`, on branch `lane/deliverables/qollab-page-research`.
- Every claim in the note has a URL and a read date. The observed claims have screenshots, and it is honest about what is UNKNOWN.
- Ideas are still unpicked. `docs-kit` is still running.

**What we now know (from the research note), and how it shapes our docs:**
- **Where projects run.** In the judge's browser: Pyodide, Python 3.14, Qiskit `>=2.5.2,<3`. A top-level `main.py` makes a Python project. Safari and iOS cannot run projects, so every page must say "use Chrome, Edge or Firefox 153+".
- **The write-up.** The README IS the Qollab write-up:
  - Markdown, at most 65k characters, with KaTeX.
  - The renderer uses `breaks:true`, so we write one paragraph per line and never hard-wrap.
  - A YouTube image link embeds the video.
  - The write-up must end with the verbatim line "This effort is supported by Qollab & IonQ".
  - It must disclose prior and third-party code with credit, and name the novelty-floor category the project meets.
- **Page fields.** Title, a description of at most 240 characters, About, the write-up, a thumbnail, tags, contributors, and repo and website links.
- **What judges grade.** Judges grade the **free local simulator** path, and IonQ results don't count for or against. The project must still run on IonQ's simulator to be eligible, with ONE job per run.
- **The model page:** Quantum Hackathon Soundtrack. Its shape is hook → what it shows → numbered how-to-use → how it works → files → make it yours → credits.
- **The cautionary page:** QCFlows sends readers off-platform and has an empty default write-up.

**Approach:**
1. **Now (doesn't need the ideas):**
   - (a) Research: DONE, merging now.
   - (b) `docs-kit` (running) builds the kit:
     - the root LICENSE and README skeleton;
     - the `docs/` templates;
     - the DISCLOSURE ledger;
     - the style guide.

     When it reports, I check that its page template follows research §6. If not, a short reconcile worker.
   - (c) Get the owner's answers to Q1 (the submission-form fields) and Q2 (does IonQ sim say Free or Credits apply when signed in?).
2. **When the owner picks the ideas:** one worker per project fills in the README/write-up, the page draft and the video script. It works from the project lane's real running output: screenshots of the built-in simulator run on Qollab, plus one IonQ-sim run if Q2 says it's free.
3. **Polish window (Oct 11, 07:00–19:00 ET):**
   - a fresh-eyes "judge" worker follows each page signed out, in Chrome, using only our docs;
   - a Markdown preview check (line breaks, KaTeX, YouTube embed) on a signed-in draft. That needs the owner or the quality lane.
   - an owner checklist for publishing and recording;
   - timing the script against 2–3 minutes.

**Done:**
- the Qollab platform and submission research, merged this consult;
- landing it on main so playground, unlocked, ux and quality can read the build constraints.

**Next:**
- judge `docs-kit` against research §6;
- relay the owner's Q1 and Q2 answers into the templates;
- start phase 2 the moment the ideas are picked.

**Risks:**
- **Q2 is unresolved.** The live dialog labels IonQ sims "Credits apply" while the docs say Free. That blocks the IonQ wording and possibly eligibility. If it costs credits, we don't press it, by the owner's ruling.
- **The Markdown behaviours were read from the bundle, not tested.** They need a signed-in draft preview before the final.
- **Build constraints may reach the project lanes too late:** one IonQ job per run, no `input()`, one-line annotated `def main`, data paths as string literals. Landing the note mitigates this.
- **Ideas could come late**, which squeezes phase 2.
- **Claims the code doesn't support:** every claim must be checked against the real run.
=== END PLAN ===

=== MERGE branch=lane/deliverables/qollab-page-research ===

=== LAND branch=lane/deliverables/integration ===

=== ASK_OWNER ===
Two signed-in checks, about 2 minutes each. Only you can do them, because they need your Qollab account. We have not signed in or submitted anything.

**Q1. The submission form.** Open `https://qollab.xyz/programs/hackathon/register` while signed in, and tell us (or screenshot) which fields it asks for. In particular: video URL, repo URL, theme, prior-code disclosure, which projects it lists, and any text-length limits. Our page drafts will match those fields exactly.

**Q2. Is the IonQ simulator free for you?** Open any public project, for example `https://qollab.xyz/u/qollab/quantum-teleportation`, and press **Run on Qollab** while signed in. Look at the "Remotely Run Simulators" rows (IonQ Aria 1, Forte 1, …). Do they say **Free** or **Credits apply**? What is your credit balance? Signed out, they show "Credits apply", while Qollab's docs say these simulators are free; see [the signed-out dialog](renders/qollab-page-research/qollab-select-qpu-signed-out.png). Eligibility requires that each project runs on IonQ's simulator, and your ruling is free simulators only. So if it says Credits apply, please don't press Run, and tell us whether hackathon teams get free IonQ-simulator access (for example, from Qollab's Slack).

For your information, no action needed: I am landing the research note on main, so every lane sees the build constraints. Judges grade the free built-in simulator, the code runs in the judge's browser (not Safari), and IonQ allows one job per run.
=== END ASK ===

=== LEARN ===
2026-10-10 consult 2: I merged qollab-page-research and landed it on main (evidence: `vault/Research/qollab-platform-and-submission.md` and `renders/qollab-page-research/*.png`).
- **The README is the write-up.** On Qollab the top-level README.md becomes the project's write-up (marked with `breaks:true`), so docs must be one paragraph per line with no hard wraps.
- **Required in every write-up:**
  - the verbatim "This effort is supported by Qollab & IonQ";
  - the disclosure of prior and third-party code;
  - the novelty-floor category the project meets;
  - "use Chrome, Edge or Firefox 153+, not Safari or iOS".
- **What judges grade.** They grade the free built-in or local simulator path. The IonQ simulator must work for eligibility, with one job per run.
- **Open question.** The IonQ-sim cost label (Free vs "Credits apply") is unresolved and with the owner (Q2). Don't write "free on IonQ" until it is answered.
=== END LEARN ===

=== LEARN ===
2026-10-10 consult 2: The model write-up is Quantum Hackathon Soundtrack: hook → what it shows → numbered how-to-use → how it works → files → make it yours → credits. Templates follow that shape.
- Avoid the QCFlows failure modes: an empty default-version write-up, and sending readers off-platform.
- **Unverified.** The Markdown behaviours (YouTube embed, KaTeX, `breaks:true`, whether raw HTML is sanitised) were read from Qollab's JS bundle, not tested. Before the final, a signed-in draft Preview (owner or quality lane, no publish) must confirm them.
=== END LEARN ===
