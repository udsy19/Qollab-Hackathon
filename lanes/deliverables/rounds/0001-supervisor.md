=== PLAN ===
**Lane goal:** Produce everything the judges read, for both projects (Playground and Unlocked):
- an MIT LICENSE;
- a README;
- a Qollab project-page draft covering what the project does, the quantum idea, how to run it on Qollab (free simulators including IonQ), and disclosure of prior and third-party code;
- a 2–3 minute demo-video script and shot list that the owner can record.

Documentation quality is one of the four judged traits, and we aim to have the best in the hackathon. We write only in `docs/`, the READMEs and the LICENSEs, and we never touch project code. The owner publishes to Qollab and posts the video.

**Where things stand (consult 1, 2026-10-10 00:49 UTC, about 20:49 ET Oct 9):**
- The owner has not picked the ideas yet; the project lanes pitch first.
- The repo has no project code yet.
- Nobody knows yet how Qollab runs projects or what a project page looks like.
- So the content of the deliverables can't be written yet. What can be done now is everything that doesn't depend on the idea: research on the format, templates, the licences and the disclosure ledger.

**Approach, in three phases:**
1. **Now (doesn't need the ideas):**
   - (a) Research how Qollab works and what a winning page looks like: the project-page format and fields, how a project runs there, submission mechanics, what judges see first, and real Qollab project pages as examples. Findings go to `vault/Research/`.
   - (b) Build the documentation kit:
     - root MIT LICENSE;
     - a root README skeleton that indexes both projects;
     - the `docs/` templates (project README, Qollab page, video script and shot list);
     - `docs/DISCLOSURE.md`, a prior and third-party code ledger with timestamps against the build window;
     - a docs style guide.
2. **When the owner picks the ideas:** one worker per project fills in the README, the page draft and the video script. Each one works from the project lane's real running output (screenshots and plots taken from the real Qollab or IonQ simulator path) and writes no claims it hasn't seen run.
3. **Polish window (Oct 11, 07:00–19:00 ET):**
   - a fresh-eyes reviewer follows each page as a judge would and presses Run following only our docs;
   - we write an owner checklist for publishing and recording;
   - we time the script against 2–3 minutes.

**Done:** nothing yet.

**Next:** dispatch `qollab-page-research` and `docs-kit`, both running now.

**Risks:**
- Qollab's format is unknown. Templates written before the research may need reshaping, so the docs-kit worker reads the research when it lands, and I will reconcile the two.
- Ideas could arrive late, which squeezes phase 2. The templates must make filling in a project a matter of hours.
- Writing claims the code doesn't support. Every claim must be checked against the running product.
- Disclosure gaps would make us ineligible. The ledger has to start now.
- Lane overlap: playground and unlocked own their own directories. We create LICENSE and README files in their directories only after those directories exist, and we coordinate through the plan. Shared Qollab research goes to `vault/Research/` so other lanes can read it.
=== END PLAN ===

=== AGENT name=qollab-page-research model=opus base=lane/deliverables/integration ===
**GOAL:** We need to know, with sources, exactly what a judge sees and does on Qollab, so our documentation is shaped for that surface and not for a generic GitHub repo. Find out four things:
- what a Qollab project page is: its fields, length limits, markdown and media support, how code and notebooks attach, how "Run" works, and the runtime (Python and Qiskit versions, available packages, network);
- how a project reaches IonQ's free simulator from Qollab (credentials and environment variables, or a built-in backend?);
- how submission works for the Qollab x IonQ hackathon (where the video link goes, required fields, disclosure of prior code);
- what the best existing Qollab projects and pages look like.

**VISION:** Documentation quality is a quarter of the score. The best docs in the hackathon are the ones that fit the platform the judges actually use, and that need zero friction to run.

**WHAT WE ARE BUILDING:** Two Qiskit projects (Playground theme, Unlocked theme) that run on Qollab's free simulators including IonQ's, each with an MIT licence, a Qollab project page and a 2–3 minute demo video. The deliverables lane writes the pages, READMEs and video scripts.

**WHAT HAS NOT WORKED:** Nothing has been tried yet. The project context does record that the Qollab runtime and format are unknown, and that guessing them is the risk.

**Vault first:** before you search, read:
- `vault/AGENTS.md`
- `vault/Home.md`
- `vault/Index.md`
- `vault/Missions/qollab-ionq-hackathon-2026.md`
- `.claude/rules/hackathon-eligibility.md`
- everything already in `vault/Research/`, since another lane may have written Qollab findings. If they have, extend their note instead of writing a second one (no-bloat).

**Where to start:**
- qollab.xyz: the FAQ, the hackathon page and its rules, the "Programming your first quantum circuits" lessons, and any public project pages.
- IonQ's docs on the qiskit-ionq simulator backend and free access.
- Use the defuddle skill to read pages. Read only: do not sign up, log in, submit, or create anything on any account. Owner accounts are the owner's.

**Deliver:**
1. `vault/Research/qollab-platform-and-submission.md`. Every claim carries its source URL and the date you read it. Mark as UNKNOWN anything you could not establish, and say what would settle it. If the owner needs to look at something while logged in, write it as a short question for them.
2. Inside that note, a section called "Implications for our docs". It lists the project-page fields we must fill and their limits, the exact run instructions a judge would follow, and what goes in the video versus the page.
3. Two or three exemplar Qollab project pages (or the closest equivalent hackathon pages). For each, a screenshot under `renders/deliverables/research/`, plus one line on what makes it good or weak.
4. A link from the Research hub (`node scripts/vault-hubs.mjs`).

**How I'll judge it:** I'll check that the sources are real and cited, that the unknowns are named rather than guessed, and that the screenshots exist. The real test is whether I can write the page template straight from your note.

**Report:** `reports/qollab-page-research.md`. It opens with a Vault check, then gives the TL;DR, the findings, the unknowns and the questions for the owner. Write a checkpoint report within 1 hour even if the work is partial, marked PARTIAL.
=== END AGENT ===

=== AGENT name=docs-kit model=opus base=lane/deliverables/integration ===
**GOAL:** Build the documentation kit, so that the moment the owner picks the two ideas, a worker can produce a top-tier README, Qollab page draft and demo-video script for each project in a few hours, and nothing eligibility-critical is forgotten.

**VISION:** Documentation quality is a judged trait, and we want the best docs in the hackathon. Judges skim: in the first screen they should understand what the project does, why it's quantum, and how to press Run. The eligibility items (MIT licence, disclosure of prior and third-party code, run instructions for the free simulators including IonQ) must never depend on someone remembering them.

**WHAT WE ARE BUILDING:** Two Qiskit projects for the Qollab x IonQ hackathon, one in Quantum Playground (playful, artistic) and one in Quantum Unlocked (make hard quantum ideas click). The build window is 2026-10-09 19:00 ET to 2026-10-11 19:00 ET. The ideas aren't picked yet, so everything you write must be independent of the idea.

**WHAT HAS NOT WORKED:** Nothing has been tried yet. Org-wide failures to avoid:
- meta-work instead of product work: keep the kit lean, with no generators, no tooling and no gates beyond what's needed;
- claims the product doesn't support.

**Vault first:** read:
- `vault/AGENTS.md`
- `vault/Home.md`
- `vault/Index.md`
- `vault/Missions/qollab-ionq-hackathon-2026.md`
- `.claude/rules/hackathon-eligibility.md`
- `vault/Research/`

A parallel worker (`qollab-page-research`) is writing `vault/Research/qollab-platform-and-submission.md`. If it lands while you work, shape the Qollab page template to its field list. If it hasn't, leave clearly marked `<!-- TODO(qollab-format) -->` spots in the template; don't guess.

**Deliver** (only in `docs/`, the root `README.md` and the root `LICENSE`; do not create `playground/` or `unlocked/`, which belong to other lanes):
1. A root `LICENSE`: standard MIT text, `Copyright (c) 2026 Udaya Tejas`.
2. A root `README.md` skeleton: a one-line pitch of the repo and a card for each project, with placeholders for the name, one-line hook, hero image, Run on Qollab link and theme. It also covers: built for the Qollab x IonQ hackathon, free simulators only, the licence, and the disclosure.
3. `docs/templates/project-README.md`, structured in this order:
   - hook and hero image;
   - what you'll see;
   - the quantum idea in plain words, then precisely;
   - run it on Qollab (IonQ simulator) in three steps or fewer;
   - run it locally;
   - how it works (the circuit, with a diagram);
   - what's novel;
   - limits and honesty;
   - credits and disclosure;
   - licence.

   Include short guidance comments for whoever fills it in.
4. `docs/templates/qollab-page.md`: the project-page draft template.
5. `docs/templates/demo-video.md`: a 2–3 minute script and shot-list template. It's a timed table (timecode, shot, on-screen, voice-over, source: which real run or screenshot it comes from), with a hook in the first 10 seconds and the live run on the IonQ simulator shown on screen. The total must be timed at about 150 words per minute.
6. `docs/DISCLOSURE.md`: a ledger of prior and third-party code. It already names Qiskit, qiskit-ionq and the agent-org tooling layer. Find from git when the org layer was committed relative to the window, and state it as you find it. It has a table that the project lanes add rows to.
7. `docs/STYLE.md`: a one-page writing guide. Plain words, no unexplained jargon, every claim backed by a run, image alt text, consistent names.

**How I'll judge it:** I'll read each template as if I were filling it in for a made-up example project. If I'm left guessing anywhere, or an eligibility item can be skipped, it fails. Show this yourself: fill the README template for a toy example (a Bell-state "quantum coin") in `docs/templates/EXAMPLE-filled.md`, then render it with any markdown previewer or a headless browser and save a screenshot under `renders/deliverables/docs-kit/`. Keep the whole kit concise; templates that bloat get cut.

**Report:** `reports/docs-kit.md`. It opens with a Vault check, then gives the TL;DR, the files with their paths, the screenshot paths, and the open TODOs that wait on the Qollab research. Commit to your branch. Write a checkpoint within 1 hour.
=== END AGENT ===

=== LEARN ===
At consult 1 (2026-10-10 00:49 UTC) the ideas are unpicked and the Qollab page and runtime format are unknown. The deliverables lane's first useful moves are therefore the idea-independent ones: research the format, build the templates and licence, and start the disclosure ledger. Per-project content waits for the owner's pick and the project lanes' running output. Don't create files under `playground/` or `unlocked/` before those lanes create the directories.
=== END LEARN ===
