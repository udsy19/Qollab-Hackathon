# Qollab-Hackathon

Our entries for the **Qollab x IonQ Quantum Hackathon** (build window 2026-10-09 19:00 ET to 2026-10-11 19:00 ET): three Qiskit projects, one per track (Quantum Impact, Quantum Playground, Quantum Unlocked), that run on Qollab's free simulators, including IonQ's.

> The projects are being defined. Each one will live in its own top-level folder, and this page will link to it and to its Qollab page.

## Projects

| project | theme | Qollab page | demo video |
|---|---|---|---|
| *(to come)* | Quantum Impact | — | — |
| *(to come)* | Quantum Playground | — | — |
| *(to come)* | Quantum Unlocked | — | — |

## How this repo maps to Qollab

Each project is a **self-contained top-level folder** that is uploaded to Qollab as is ("Upload your own files"). Qollab runs it in the browser (Pyodide, Python 3.14, Qiskit 2.x), so a project folder holds:

- `main.py` (a Python project) or `index.html` + `main.js` (a JS project), at the folder's top level;
- `requirements.txt`, one `name` or `name<op>version` per line;
- `LICENSE` (MIT);
- `README.md`, which becomes the Qollab project page, written one paragraph per line.

New projects start from `templates/qollab-project/`, which already follows every rule below. The full research behind these rules is `vault/Research/qollab-platform-and-submission.md`.

## The hackathon requirements, and how we hold ourselves to them

| requirement | how it is met | checked by |
|---|---|---|
| Qiskit project, runs on Qollab's free simulators including IonQ's | uses the `backend` Qollab pre-creates, never its own; one `backend.run` per run (IonQ allows one job per run) | `qollab-submission.mjs` + a real run on Qollab |
| Published and runnable on Qollab under MIT | `LICENSE` in the repo and in every project folder | `qollab-submission.mjs` |
| A project page: what it does, how to run it, how to extend it | each project's `README.md`, from the template's sections | `qollab-submission.mjs` |
| Built during the window, prior code disclosed | a "Built during the hackathon / prior work" section on every page | `qollab-submission.mjs` (presence) + review |
| Beyond tutorial level (the novelty floor) | a "What's new here" section naming the category claimed | `qollab-submission.mjs` (presence) + review |
| A 2-3 minute demo video at a public link | a YouTube link on the page (the only host it can embed) | `qollab-submission.mjs` (presence); public access by hand |
| Attribution: "This effort is supported by Qollab & IonQ" | verbatim on every project page | `qollab-submission.mjs` |
| UI accessibility best practice | an Accessibility section, and checked by looking | review |
| No secrets, no paid compute | no API keys in code; free simulators only | `qollab-submission.mjs` (keys); owner rule |

Run the checks:

```bash
node scripts/gates/qollab-submission.mjs              # every project folder
node scripts/gates/qollab-submission.mjs --selftest   # proves the checker catches each broken rule
```

## What else is in this repo

`vault/`, `scripts/`, `.claude/` and `evidence/` are our development tooling: an Obsidian vault used as the team's notes and plan, and the scripts and agent configuration that keep the work organised. They are not part of any submitted project. The tooling comes from a kit the owner wrote before the hackathon, and it is disclosed here as prior work. Each project folder discloses its own prior work on its page.

## License

MIT. See `LICENSE`.

This effort is supported by Qollab & IonQ
