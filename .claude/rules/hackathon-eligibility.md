# Hackathon eligibility (owner ruling, 2026-10-09)

The mission is the Qollab x IonQ hackathon. A project that misses any of these cannot win, so
treat each as a hard requirement, not a nice-to-have:

1. **Qiskit, on free simulators only.** Every project is a Qiskit project that runs on Qollab's
   free simulators, including IonQ's quantum simulator. Owner: "Free simulators only" — no paid
   QPU jobs, no paid cloud compute, no services that need a card. Never submit a job that costs money.
2. **MIT licensed, runnable on Qollab.** Each project carries an MIT `LICENSE` and runs on Qollab
   as published; judges press Run, so the Qollab path is the real path to prove.
3. **Project page.** Each project has a Qollab project page explaining what it does and how to run it.
4. **Built in the window.** Work happens Oct 9 19:00 ET → Oct 11 19:00 ET. Any pre-existing code
   or third-party code is disclosed in the project page; judging is on what we add.
5. **Demo video.** A 2–3 minute demo video at a public link with no sign-in.
6. **Deadline is hard:** submissions close 2026-10-11 19:00 ET. Anything not shippable by then is cut.

7. **Attribution, verbatim, on every project page:** "This effort is supported by Qollab & IonQ".
   Code and docs stay MIT and the project stays on Qollab for 12 months (terms).
8. **Beyond tutorial level.** A project must claim at least one of: a novel application context,
   a technical extension (noise mitigation, parameter optimisation, comparative benchmarking), or an
   original analytical or educational contribution. Otherwise judges may score 0 on novelty and
   execution. The page names the category it claims.
9. **UI accessibility best practice** (terms): keyboard use, contrast, text alternatives.

**How Qollab runs a project** (`vault/Research/qollab-platform-and-submission.md`): each project is a
self-contained top-level folder, uploaded as is. It runs in the judge's browser (Pyodide, Python 3.14,
Qiskit 2.x), uses the `backend` Qollab pre-creates (never its own), and sends at most ONE job per run on
IonQ. Its `README.md` becomes the project page, one paragraph per line. Judges grade on the free local
simulator, so that path must be flawless. Safari cannot run Qollab projects. Start every project from
`templates/qollab-project/`, and keep `node scripts/gates/qollab-submission.mjs` green: it checks
every rule here that can be read from the files.

Judged on four traits, equally: novelty & creativity, technical execution, impact potential,
documentation quality. Optimise for all four, judged by looking at the running project.

**Owner-only actions:** publishing to Qollab, uploading/posting the demo video, and anything that
needs the owner's accounts. Agents prepare the material; the owner publishes. Pushing `main` to
GitHub deploys nothing and is allowed.
