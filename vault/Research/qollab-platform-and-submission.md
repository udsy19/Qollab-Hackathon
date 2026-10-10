---
type: research
status: current
date: 2026-10-09
updated: 2026-10-09
owner: deliverables
tags:
  - qollab
  - hackathon
  - docs
---

# Qollab platform, runtime and hackathon submission: what a judge sees and does

Qollab runs each project **in the judge's browser** (Pyodide, Python 3.14, Qiskit 2.x). It hands the code a pre-made
`backend` chosen in a **Select QPU** dialog, and it turns a top-level `README.md` into the project's Markdown write-up.
A judge opens `qollab.xyz/u/<user>/<project>`, reads the Project Card, presses **Run on Qollab**, picks a free
simulator, and reads the console. Our docs are shaped for that path, not for a GitHub repo.

**How this was read.** Every Qollab page below was rendered with headless Chrome on **2026-10-09** (ET evening) and
extracted with defuddle. qollab.xyz is a Nuxt SPA, so a plain fetch returns an empty shell. "Observed" means I saw it
in the live product, signed out, with the screenshot path given. "Bundle" means it was read from Qollab's shipped JS
(`/_nuxt/CB-2i0Mk.js`, fetched 2026-10-09), which is code and not documentation. Nothing was signed up for, logged
into, submitted or created.

## 1. The runtime: where and how code runs

| fact | source (read 2026-10-09) |
|---|---|
| Code runs in the browser. Python runs on **Pyodide** (WASM); a JS project's JavaScript runs in the page. Nothing runs on a server except the quantum job on IonQ's servers when a remote backend is picked. | https://qollab.xyz/learn/docs/runtime-environment |
| **Python 3.14 with Qiskit 2.x**, NumPy 2.x, most of the stdlib. | https://qollab.xyz/learn/docs/python-qiskit-projects |
| The project type is decided by top-level files on every Run. `index.html` + `main.js` make a **JS project** (and win if all three are present). Otherwise `main.py` makes a **Python project**. With neither, Run is disabled. Files in folders do not count (`app/main.py` is not an entry point). | runtime-environment |
| `requirements.txt` takes one requirement per line (`name==x` or a range). Pip options, env markers and URL requirements are refused. If Qiskit is not named, the runtime adds `qiskit>=2.5.2,<3.0.0`. NumPy, SciPy and Matplotlib come with Pyodide. Any pure-Python wheel, or any package Pyodide has built, installs. A package needing compiled code without a Pyodide build stops the run. | runtime-environment § Libraries |
| Optional "Libraries" toggles: Qiskit Visualizations (needed for `draw("mpl")`), Algorithms 0.4.0, Optimization 0.7.0, Nature 0.8.0 + PySCF, Finance 0.4.1, Machine Learning 0.9.1, QAVE 0.1.0, PQCA 2.1.0a1 (+ `qiskit_aer==0.17.2`). | runtime-environment § Libraries |
| `main.py` runs top to bottom. **`input()` does not work.** If `main.py` defines `def main(...)` with every parameter annotated `int`/`float`/`str`/`bool` and the whole signature on one line starting at column 0, the runtime calls it, and the parameters become a **Run settings** form in the Select QPU dialog. If the signature breaks a rule, no form appears, `main()` is **silently not called**, and nothing warns you. | runtime-environment § Python projects |
| `plt.show()` renders an SVG in the console. `plt.savefig("x.png")` shows it and offers a download. `from js import sendFile` puts any file (JSON, image, LaTeX) in the console. | runtime-environment |
| **Network:** GET only (`pyodide.http.pyfetch`, `fetch`). The server must allow CORS. A JS project's origin is `null`. POST/PUT/DELETE, XHR, WebSocket and web workers are blocked. | runtime-environment § Network access |
| **No persistence between runs**, including `localStorage` and cookies in a JS project. Ship saved state as a project file. | runtime-environment § Saving data |
| Data files load only if their path appears **as a plain string literal** in the Python code. Paths built with f-strings, `+` or `os.path.join` are not loaded and fail with `OSError`. JS cannot read project files; read them in Python and return them to JS. | runtime-environment § Data files |
| **Limits:** 100 files per project, 2 MB per file, 200 MB across all a user's projects. No run time limit. Stop gives Python 5 s. | runtime-environment § Limits; https://qollab.xyz/learn/docs/upload-your-files |
| JS projects: `index.html` is body content only. `<script>` tags do not run. `main.css` is the only stylesheet loaded. `three` 0.186.1 and `postprocessing` 6.39.5 are importable by name. Anything else comes by full URL (e.g. jsdelivr `+esm`). JS calls Python modules via `import * as m from 'pkg.mod'` and `m.fn.callPromising(...)`. A plain call on an IonQ backend fails with `ConnectionError ... XHR`. | runtime-environment; https://qollab.xyz/learn/docs/js-qiskit-projects |
| **Browsers:** a recent Chrome, Edge, Brave or Opera, or Firefox 153+. **Safari cannot run projects** (no WebAssembly JSPI), and neither can any browser on iPhone or iPad. | runtime-environment § Browser support; https://qollab.xyz/programs/hackathon/how-it-works (FAQ) |

## 2. Reaching IonQ's simulator: a built-in backend with no credentials

- **No API key and no environment variable.** `backend` is a pre-created global in `main.py`, and is available in
  `main.js` and every JS file it imports. Whoever presses Run picks it in Select QPU. "Do not create or hardcode a
  backend yourself, or the project ignores the choice made in the dialog." Sources:
  https://qollab.xyz/learn/docs/runtime-environment § The backend variable, and
  https://qollab.xyz/learn/docs/python-qiskit-projects § The pre-created backend.
- `backend` is the real provider object: Qiskit's `BasicSimulator` for the built-in simulator, an IBM `Fake*` backend
  for the noise models, and `IonQProvider`'s backend for IonQ. Its default is 1024 shots. Source: python-qiskit-projects.
- **One job per run on any IonQ backend**, simulator or hardware. A second `backend.run` stops the run with an error.
  Put every circuit into one `backend.run` call, or pack them side by side on separate qubits in one circuit, as
  Quantum Hackathon Soundtrack does. Local simulators take unlimited jobs. Sources: runtime-environment § One job per run on
  IonQ, and https://qollab.xyz/learn/docs/compute-backends.
- **The backends** (from compute-backends):
  - Built-in simulator: 24 qubits, ideal, in the browser, free.
  - AWS Braket local simulator: 25 qubits, in the browser, free.
  - Eight IBM noise-model simulators: 120–156 qubits, in the browser, free.
  - Four IonQ **remote** noise-model simulators on IonQ's cloud: Aria 1 and Aria 2 at 25 qubits, Forte 1 and Forte
    Enterprise 1 at 29 qubits, documented as "Free". IonQ's noise simulation runs once per shot, so it slows down with
    the shot count.
  - IonQ hardware: 36 qubits, costs credits.
- The local `qiskit-ionq` path (an `IONQ_API_KEY` env var plus `IonQProvider()`) is only for running **off** Qollab.
  Source: https://qollab.xyz/learn/quantum-computing-with-python/ionq-setup. We do not need it on Qollab, and must never
  put a key in published code.
- **The docs and the live product disagree (observed).** Signed out, the live Select QPU dialog labels all four IonQ
  remote simulators **"Credits apply"**, while the built-in, AWS and IBM rows say "Free". Screenshot:
  `/Users/udsy/agent-org/lanes/deliverables/renders/research/qollab-select-qpu-signed-out.png`. The docs say they are
  free (compute-backends, https://qollab.xyz/learn/docs/how-credits-work, the FAQ). **UNKNOWN** whether a signed-in
  account sees "Free". I did not press Run on an IonQ row, because the label says credits.
- **Who runs what.** The terms say "Judges run every project on a **free local simulator**, and results from IonQ's
  simulators or hardware neither add nor subtract points" (https://qollab.xyz/programs/hackathon/terms). The FAQ adds:
  "A project that runs on an IonQ simulator has to fit one job per run, so press Run there before you submit"
  (how-it-works). **Consequence: the built-in simulator path is the one judges grade, and it must be flawless. The
  IonQ-simulator path must also work, because eligibility requires it.**
- **Observed, signed out:** "Run on Qollab" on `/u/qollab/quantum-teleportation`, then the Built-in simulator, then Run.
  It completed in 2.1 s with the console showing "Loading packages… Loading project files… Compiling / initializing
  runtime… Running…", the text circuit drawing, and a Probabilities panel. **A judge does not need to sign in to run a
  project on the built-in simulator.** Screenshot:
  `/Users/udsy/agent-org/lanes/deliverables/renders/research/qollab-run-builtin-signed-out.png`.

## 3. The project page: fields, limits, Markdown, media

**The layout** (https://qollab.xyz/learn/docs/project-anatomy):
- **Tabs:** Project Card, Code, and Discussions once published.
- **Main column:** title, an optional thumbnail, and the write-up.
- **Sidebar:** Contributors, Tags, **About** (the summary shown on the project card), Project Versions, Repository and
  Website links.
- **Header:** Run on Qollab, Fork, Like, Share and Edit.

The public URL is `qollab.xyz/u/<username>/<project>`.

| field | limit / behaviour | source |
|---|---|---|
| Project Title | renamable via the pencil, which also changes the URL slug | project-anatomy; https://qollab.xyz/learn/building-your-first-qollab-project/create-project |
| Project description (at creation) | **≤ 240 characters** | create-project |
| About (sidebar summary) | shown on the project card. **UNKNOWN** whether it is the same field as the 240-character description, and its limit | project-anatomy |
| Write-up | **Markdown**, with a Write/Preview toggle and a math button. A top-level `README.md` **becomes** the write-up when a project is created from an upload, **≤ 65,000 characters** (a longer one is refused). On upload into an *existing* project, `README.md` is skipped: paste it into the write-up row instead | https://qollab.xyz/learn/docs/write-your-project-page; upload-your-files |
| Thumbnail | optional image, drag and drop. A default is used if absent | write-your-project-page |
| Tags | free topics, e.g. `qiskit`, `ionq`. The language chip ("Python + Qiskit") is shown automatically (observed) | write-your-project-page |
| Contributors | add collaborators | write-your-project-page |
| Links | a **Git repository** and a **project website** | write-your-project-page |
| Version | Publish → Version name, optional Release notes, Visibility. Versions are immutable. Max 10 publishes per hour. The project is public only once a version is **public and the default** | https://qollab.xyz/learn/docs/publish |

**Markdown rendering, from the bundle** (code, not docs; verify each in Preview before relying on it):
- The renderer is `marked` with `{gfm: true, breaks: true}`. **A single newline becomes a line break**, so a README
  hard-wrapped at 100 or 120 columns will render as ragged short lines. **Write the write-up with one paragraph per
  line.**
- Image syntax with a **YouTube URL** (`![caption](https://youtu.be/<id>)`) is rendered as an embedded 16:9 YouTube
  iframe in a `<figure>` with that caption.
- An image link ending in `.mp4`, `.webm`, `.mov` or `.ogg` becomes a `<video controls>`. Links to other sites open in
  a new tab.
- KaTeX is bundled, which matches the documented math button. Observed: the QCFlows page renders `$K_{i\to j}$`.
- The headings become a left-hand table of contents. Observed on Soundtrack (H2s) and on Teleportation (H3s numbered
  "1. Introduction" …).
- **The site CSP limits media hosts** (`curl -sI https://qollab.xyz/u/qollab/quantum-teleportation`, 2026-10-09):
  - Images and video files load only from Qollab's own hosts (`api.cms.qollab.xyz`, `pub.qollab.xyz`), `github.com`,
    `raw.githubusercontent.com`, `data:` and `blob:`.
  - The only video frames allowed are `www.youtube.com` (plus Google and Qollab).
  - **So the demo video can embed only from YouTube.** Loom, Vimeo and Drive must be plain links. Images must be
    uploaded to Qollab or served from our public GitHub repo's raw URLs.
- **UNKNOWN:** whether raw HTML in the write-up is sanitised; whether a write-up image can point at a project file
  (an `/assets/` path gets the CMS prefix, per the bundle); and the thumbnail's size or aspect ratio. The QCFlows
  sitemap image suggests a CMS asset; the og:image is 1200×630.

**How code attaches.** See create-project, upload-your-files and https://qollab.xyz/learn/docs/fork-and-remix.
- **New Project** offers three shapes: Python / Qiskit, JS / Qiskit wrapper, or **Upload your own files**. Upload
  accepts files, a folder, or `.zip` / `.tar*`.
- A single wrapping folder is stripped, so a GitHub "Download ZIP" lands `main.py` at the top level.
- `.git`, `__MACOSX` and `.DS_Store` are dropped, and `requirements.txt` is added if missing.
- **Notebooks: UNKNOWN / effectively unsupported.** No doc mentions `.ipynb`. Only `main.py` or `index.html` +
  `main.js` can run, so a notebook would be an inert file.
- There is no GitHub sync. The repo is just a sidebar link.

## 4. Hackathon submission (Qollab x IonQ, 2026-10-09 → 10-11)

Sources: https://qollab.xyz/programs/hackathon, https://qollab.xyz/programs/hackathon/how-it-works (FAQ), and
https://qollab.xyz/programs/hackathon/terms.

- **Who and where.** The **team captain** submits from the registration page (`/programs/hackathon/register`, signed
  in), between Oct 9 19:00 ET and **Oct 11 19:00 ET**.
  - A team can submit **up to 5 projects**, each public and owned by the captain or a teammate.
  - The captain can edit a submission until the deadline. After it, they can only withdraw.
  - The **theme is declared at submission** and can be changed until the deadline.
- **Eligibility.** A project must:
  - be a Qiskit project that runs on Qollab's free simulators, including IonQ's;
  - be **published and runnable on Qollab under MIT** before the deadline (any outside repo it relies on must also be
    MIT, public, sign-in-free, with its dependencies listed and no secrets);
  - have a **Qollab project page** "covering what the submission does, what problem it explores, how to run it, and
    other information to enable others to understand, replicate, or extend it";
  - be built in the window, with prior code disclosed;
  - have a 2–3 minute demo video at a public, no-sign-in link;
  - **"Follow industry best practices on UI accessibility"** (terms).
- **Mandatory attribution (terms § Participant obligations).** Include on the project: **"This effort is supported by
  Qollab & IonQ"**. Also: release code and docs under MIT, and keep the project on Qollab for 12 months.
- **Disclosure of prior code.** "Say on your project page what existed before the build window and credit its
  source, such as a fork, template, repo or tutorial." Undisclosed reuse is grounds for disqualification. Qollab's
  model examples are the forks QCFlows Multi-file and Quantum Hackathon Soundtrack, which "name their original in the
  project description" (how-it-works FAQ). AI tools are allowed.
- **Novelty floor (terms).** A project must go beyond a reference or tutorial-level implementation, with at least one
  of: a novel application context; a technical extension (noise mitigation, parameter optimisation, comparative
  benchmarking); or an original analytical or educational contribution. Panels may score **0** on novelty and technical
  execution if this bar is not met. **The page should name which one we claim.**
- **The video.** It "shows the project working". "A screen recording with a voiceover is enough", and we do not need
  to appear on camera. Host it on YouTube, Loom, Vimeo or Google Drive, viewable by anyone with the link.
- **Judging.** Four traits, equally weighted:
  - Novelty & creativity
  - Technical execution
  - Impact potential
  - Documentation quality

  A local panel scores first, then a global panel re-scores the top entries. **Best Documentation** is its own
  specialty award ($500 + $5,000 compute).
- **UNKNOWN (behind login):** the submission form's fields — where the video URL goes, whether it asks for a repo
  link, a theme, a disclosure field or a team-member list, and whether it pulls the project by URL or by picker. This
  is owner question Q1.

## 5. Exemplar pages

Screenshots are in `/Users/udsy/agent-org/lanes/deliverables/renders/research/`, captured at 1440×2600 with headless
Chrome on 2026-10-09.

| page | screenshot | verdict |
|---|---|---|
| [Quantum Hackathon Soundtrack](https://qollab.xyz/u/qollab/quantum-hackathon-soundtrack) (Qollab's own hackathon showcase, v1.1, Oct 9 2026) | `exemplar-quantum-hackathon-soundtrack.png` | **The model to copy.** A one-paragraph hook, then *What it shows* → *How to use it* (numbered steps naming the exact buttons, and "No credits needed" up front) → *How it works* (a concept → circuit → effect table, plus the one-job-per-run design stated openly) → a file tree → *Make it yours* (fork recipes naming the constants to edit) → *Credits* (the fork disclosed with its link and licence). Weak: no thumbnail or video at the top. |
| [Quantum Teleportation](https://qollab.xyz/u/qollab/quantum-teleportation) (Qollab example) | `exemplar-quantum-teleportation.png` | **Good teaching shape for Unlocked**: numbered sections, a circuit diagram, and an *Expected Output* block that the real run reproduced (I observed P(0)=0.754 against the expected 0.750). Weak as a hackathon entry: it is a textbook protocol, so it would fail the novelty floor. |
| [QCFlows](https://qollab.xyz/u/itaborala/qcflows) (community, Spring 2026 Creative Challenge) | `exemplar-qcflows.png` | **A cautionary example.** The About text is strong and the math renders, but "How to get started" sends the reader **off-platform** to app.qcflows.net and GitHub. In my capture the default version v0.1.2 showed *"This project doesn't have a write-up yet"*, while an earlier DOM dump of the same URL contained a full write-up. A judge can land on an empty card, so **after every publish, check the default version's card while signed out.** |

## 6. Implications for our docs

**A. Fields we must fill, per project (Project Card plus publish):**

| field | what we put | limit |
|---|---|---|
| Title | the project name only | URL slug follows it, so choose it once |
| Description / About | the one-sentence hook: what it is plus which quantum idea is essential | ≤ 240 characters (UNKNOWN whether About has its own limit) |
| Thumbnail | a real frame from the running project | size UNKNOWN; aim for 1200×630 |
| Write-up | `README.md`, structured as in C below | ≤ 65,000 characters. **One paragraph per line** (`breaks: true`) |
| Tags | `qiskit`, `ionq`, the theme (`playground` / `unlocked`), the concept (`entanglement`, `error-correction`, …), `hackathon` | — |
| Contributors | every team member's Qollab account | — |
| Repository | the public MIT GitHub repo URL | — |
| Website | the video link, or leave it empty | — |
| Version | `v1.0`, release notes "Hackathon submission", **Public + default** | max 10 publishes per hour |

**B. Files at the project root:**
- `main.py` (Python), or `index.html` + `main.js` (+ `main.css`) for JS.
- `requirements.txt`, which **pins the Qiskit line we tested on** and lists only Pyodide-installable packages.
- `LICENSE` (MIT).
- `README.md`, which becomes the write-up at creation.
- Data files at most 2 MB each, at most 100 files, and no secrets.
- For a Python project, a `def main(shots: int = 1024, ...)` on **one line**, with annotated simple types, so judges
  get a Run settings form. **Do not call `main()` ourselves.** All IonQ work goes in **one `backend.run` call per run**.

**C. The write-up skeleton** (Soundtrack's order, plus the hackathon's required items):
1. A one-paragraph hook. Then the **embedded demo video**: `![2-minute demo](https://youtu.be/<id>)`, on YouTube so it
   embeds.
2. **What it shows / what you'll understand.** The quantum ideas that are *essential* (Playground), or the concept made
   intuitive (Unlocked).
3. **How to run it**, copied below, with expected output and runtime.
4. **How it works:** the circuits, a concept → circuit → effect table, and why one job per run.
5. **What's new here:** name the novelty-floor category we claim (terms).
6. **Make it yours:** fork recipes naming files and constants.
7. **Built during the hackathon / prior work:** what existed before Oct 9 19:00 ET, with source and licence, or
   "nothing: written from scratch in the window". AI-tool use disclosed.
8. **Accessibility notes** (terms require UI accessibility best practice): keyboard, contrast, text alternatives for
   sound and colour.
9. Licence: MIT (repo link). Then, verbatim: **"This effort is supported by Qollab & IonQ"**.

**D. The exact run instructions a judge follows** (put them in the write-up as written, adjusted to the project):
1. Open the page in **Chrome, Edge, Brave, Opera or Firefox 153+**. Safari and iPhone/iPad cannot run Qollab projects.
2. Press **Run on Qollab** (top right). No sign-in is needed for the free local simulators.
3. Under **Run settings**, keep the defaults (or set *Shots* …).
4. Pick **Built-in simulator (24q)** under *Locally Run Simulators* and press **Run**.
5. Expect the console to show … within N s. JS project: the interactive page appears above the console.
6. To use IonQ's simulator: Run again, pick **IonQ Forte 1 (29q)** under *Remotely Run Simulators*. The project sends
   exactly one job. Wording depends on Q2 below.
7. Press **Stop** when done (for JS projects that keep playing).

**E. Video vs. page.**
- **The video (2–3 min)** shows the real Qollab page:
  - the hook (≤ 15 s);
  - pressing *Run on Qollab*, choosing a simulator, and the result appearing;
  - the interaction or the "click" moment;
  - one IonQ-simulator run;
  - a closing line on what is new.

  It is a screen recording with voiceover, public, on **YouTube** (the only host the page can embed).
- **The page** carries everything the video cannot: the run steps, the theory, the circuit table, the novelty
  category, the disclosure, the fork recipes, the licence and the attribution. Judges grade the page and the run
  directly, so the page must stand without the video.

## 7. UNKNOWNs and what would settle them

| unknown | what settles it |
|---|---|
| Fields of the hackathon submission form (video URL, repo, theme, disclosure) | the owner opens `/programs/hackathon/register` signed in and lists the fields (Q1) |
| Do the IonQ remote simulators show "Free" when signed in, or "Credits apply" as they do signed out? | the owner opens any project's Select QPU dialog signed in (Q2) |
| Does a pure-Python `main.py` run on an IonQ remote backend? (Soundtrack says "remote backends only work from JS while the run is active"; python-qiskit-projects implies Python works) | the quality lane runs a 2-qubit `main.py` on IonQ Forte 1 in a signed-in draft, once Q2 confirms it is free |
| Whether the write-up honours YouTube embeds and `breaks: true` as the bundle suggests | paste a test write-up into a draft and use **Preview** (no publish needed) |
| About-field limit; thumbnail size; HTML sanitising; project-file images in the write-up | the same draft, in Preview |
| `.ipynb` support | assume none; no doc mentions it |

## Related

- Mission: [[Missions/qollab-ionq-hackathon-2026]]
- Eligibility law: `.claude/rules/hackathon-eligibility.md`
