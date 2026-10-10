## TL;DR

- **Done.** The cited note is `vault/Research/qollab-platform-and-submission.md` (commit `ddbe953` on `lane/deliverables/qollab-page-research`). It includes "Implications for our docs", with the field table, write-up skeleton, judge run steps and video-vs-page split. The page template can be written straight from §6.
- **Runtime.** Projects run **in the judge's browser**: Pyodide, Python 3.14, Qiskit `>=2.5.2,<3`. A top-level `main.py` makes a Python project; `index.html` + `main.js` make a JS project. **Safari cannot run Qollab projects.** There is no `input()`, no persistence, GET-only network, and limits of 100 files at 2 MB each.
- **IonQ access.** No API key and no env var: a `backend` global comes from the Select QPU dialog. **IonQ backends accept ONE job per run.**
- **Write-up.** `README.md` becomes the write-up (Markdown, ≤ 65,000 characters, KaTeX). The renderer uses `breaks: true` (from the bundle), so **don't hard-wrap**. A `![..](youtube URL)` embeds the video, and YouTube is the only embeddable host.
- **Hackathon must-haves.** The verbatim line **"This effort is supported by Qollab & IonQ"**. Disclosure of prior code with credit. UI accessibility best practice. The page names which novelty-floor category it meets, or risks scoring 0.
- **Signed-out run (observed).** Run on the built-in simulator works with **no sign-in** (2.1 s). The dialog labels the **IonQ remote sims "Credits apply"**, although the docs say free, so owner question Q2 is a blocker for the IonQ wording.
- **Evidence.** 5 PNGs in `renders/qollab-page-research/`: 3 exemplars, the Select QPU dialog, and a run output.
- **Recommend.** The owner answers Q1 and Q2. A worker drafts the page template from §6. Quality tests a pure-Python IonQ run.

## Vault check

- **Read:**
  - `vault/AGENTS.md`, `vault/Home.md` (NOW block), `vault/Index.md`, `vault/Missions/qollab-ionq-hackathon-2026.md`
  - `vault/Research/README.md` (empty, 0 notes), `vault/Design/lanes-and-supervisors.md` § Where research findings go
  - `vault/CLAUDE.md`, `.claude/rules/hackathon-eligibility.md`, `lanes/deliverables/context.md`
- **Already known:** only the eligibility rules, and that "the Qollab runtime and format are unknown".
- **Prior Qollab findings:** none on main or on any branch. `where.mjs qollab --branches` found nothing unlanded.
  `git diff --stat main...<b>` was empty for `lane/{playground,unlocked}/qollab-recon`,
  `lane/quality/qollab-exec-research`, `lane/ux/qollab-render-research` and `lane/unlocked/ionq-sim-spike` (checked
  ~20:50 ET). No lane reports existed.
- **Reused:** nothing to reuse, so this is the first note. The sibling recon lanes should **extend** this note rather
  than write a second one.
- **Stale or wrong:** `context.md` says to check "Qiskit/qiskit-ionq compatibility" with host Python 3.13. On Qollab,
  qiskit-ionq is not ours to install: the platform injects the backend, and its runtime is Python 3.14 / Qiskit 2.5+.
  Local venvs should pin `qiskit>=2.5.2,<3` to match.

## What I found

All of it is in the note, with a URL and the read date 2026-10-09 on every claim. The headlines:

1. **The project page.**
   - Fields: Title (renames the slug), description ≤ 240 characters, About, Markdown write-up ≤ 65k, optional
     thumbnail, Tags, Contributors, Repository and Website links.
   - Publishing is by immutable versions (name, release notes, visibility). The page is public only when a version is
     public **and the default**.
   - Code attaches by upload (files, a folder, or a zip/tar, with a single wrapping folder stripped).
   - There is no notebook support anywhere in the docs.
2. **IonQ simulator.** It is a built-in backend selected in the dialog, with no credentials. The four IonQ remote
   noise-model sims are documented as free. Each run on an IonQ backend allows one job.
3. **Submission.**
   - The captain submits from `/programs/hackathon/register`, up to 5 projects, and declares the theme at submission.
   - The video is 2–3 minutes on YouTube, Loom, Vimeo or Drive, and a screen recording with voiceover is enough.
   - The terms say judges run every project on a **free local simulator**. IonQ results neither add nor subtract
     points, but the project must still run on IonQ's sim to be eligible.
4. **Exemplars.**
   - **Quantum Hackathon Soundtrack** is the model: hook → what it shows → numbered how-to-use → how it works → files →
     make it yours → credits.
   - **Quantum Teleportation** has a good Unlocked teaching shape, but is tutorial-level.
   - **QCFlows** is cautionary: it sends readers off-platform, and its default version rendered *"This project doesn't
     have a write-up yet"* in my capture.

## Changes (commits)

- `ddbe953` research: Qollab platform, runtime, IonQ backend access and hackathon submission. It adds
  `vault/Research/qollab-platform-and-submission.md`.
- The hubs are **not** committed, per the worker rules. `node scripts/vault-hubs.mjs --check` shows Research/README
  and Map as STALE, which means they would gain this note. `vault-reachability` currently FAILS only on this note
  ("UNREACHABLE from Home.md (1): Research/qollab-platform-and-submission.md"). The loop's post-merge hub regeneration
  clears that.

## Evidence

- Screenshots, captured with headless Chrome at 1440 px on 2026-10-09:
  - `/Users/udsy/agent-org/lanes/deliverables/renders/research/` and copies in `renders/qollab-page-research/`
  - `exemplar-quantum-hackathon-soundtrack.png`, `exemplar-quantum-teleportation.png`, `exemplar-qcflows.png`
  - `qollab-select-qpu-signed-out.png`
  - `qollab-run-builtin-signed-out.png`
- Bundle evidence: `https://qollab.xyz/_nuxt/CB-2i0Mk.js` (marked `{gfm:true, breaks:true}`, the YouTube→iframe and
  `.mp4`→`<video>` image renderer, KaTeX).
- CSP evidence: `curl -sI https://qollab.xyz/u/qollab/quantum-teleportation`.
- The rendered docs are in `/tmp/qpr/md/` (scratch, not committed).

## What I did NOT do / could not verify

- **Did not sign in or submit anything.** The submission form's fields are UNKNOWN.
- **Did not press Run on an IonQ remote simulator**, because it is labelled "Credits apply" when signed out. So
  "IonQ sim is free" is documented but **not observed**, and whether pure-Python `main.py` works on IonQ is UNKNOWN.
  The Soundtrack page says "remote backends only work from JS while the run is active".
- **Markdown behaviours were read from code, not tested in a draft:** `breaks: true`, the YouTube embed, video files,
  and whether raw HTML is sanitised.
- **Two exemplar captures were dropped:** Quantum Patterns and QAVE rendered "Project not found" in screenshot mode,
  though their DOM dumps had content. I did not investigate further.
- Thumbnail size and the About-field limit are UNKNOWN.

## Questions for the owner (logged-in, about 2 minutes each)

- **Q1.** Open `qollab.xyz/programs/hackathon/register` signed in. What fields does the submission form ask for? Is
  there a video URL, repo URL, theme, prior-code disclosure, or project picker?
- **Q2.** Open any public project, press **Run on Qollab** signed in, and look at the *Remotely Run Simulators* rows
  (IonQ Forte 1 etc.). Do they say **Free** or **Credits apply**? If "Credits apply", is the credit balance 0, and does
  Qollab's Slack say the IonQ sim is free for hackathon teams?

## What the supervisor should do next

1. Send Q1 and Q2 to the owner. Q2 gates the "run it on IonQ" wording, and our free-simulators-only rule.
2. Brief a deliverables worker to write `docs/project-page-template.md` from note §6 (fields table, write-up skeleton,
   judge run steps, video-vs-page split). Every README is one-paragraph-per-line and ends with the verbatim attribution.
3. Ask the quality lane, once Q2 says free, to prove on a signed-in **draft** (no publish):
   - a 2-qubit `main.py` on IonQ Forte 1;
   - a Preview of a test write-up, checking the YouTube embed, line breaks and math.

   Then extend this note's UNKNOWN table rather than writing a new note.
4. Tell the playground and unlocked lanes the build constraints now:
   - browser Pyodide;
   - one IonQ job per run;
   - no `input()`;
   - a one-line annotated `def main(...)` for run settings;
   - files at most 2 MB;
   - data paths as string literals;
   - the built-in simulator is what judges grade.
