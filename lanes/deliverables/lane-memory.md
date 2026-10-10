
- 2026-10-10 consult 1: At consult 1 (2026-10-10 00:49 UTC) the ideas are unpicked and the Qollab page and runtime format are unknown. The deliverables lane's first useful moves are therefore the idea-independent ones: research the format, build the templates and licence, and start the disclosure ledger. Per-project content waits for the owner's pick and the project lanes' running output. Don't create files under `playground/` or `unlocked/` before those lanes create the directories.

- 2026-10-10 consult 2: 2026-10-10 consult 2: I merged qollab-page-research and landed it on main (evidence: `vault/Research/qollab-platform-and-submission.md` and `renders/qollab-page-research/*.png`).
- **The README is the write-up.** On Qollab the top-level README.md becomes the project's write-up (marked with `breaks:true`), so docs must be one paragraph per line with no hard wraps.
- **Required in every write-up:**
  - the verbatim "This effort is supported by Qollab & IonQ";
  - the disclosure of prior and third-party code;
  - the novelty-floor category the project meets;
  - "use Chrome, Edge or Firefox 153+, not Safari or iOS".
- **What judges grade.** They grade the free built-in or local simulator path. The IonQ simulator must work for eligibility, with one job per run.
- **Open question.** The IonQ-sim cost label (Free vs "Credits apply") is unresolved and with the owner (Q2). Don't write "free on IonQ" until it is answered.

- 2026-10-10 consult 2: 2026-10-10 consult 2: The model write-up is Quantum Hackathon Soundtrack: hook → what it shows → numbered how-to-use → how it works → files → make it yours → credits. Templates follow that shape.
- Avoid the QCFlows failure modes: an empty default-version write-up, and sending readers off-platform.
- **Unverified.** The Markdown behaviours (YouTube embed, KaTeX, `breaks:true`, whether raw HTML is sanitised) were read from Qollab's JS bundle, not tested. Before the final, a signed-in draft Preview (owner or quality lane, no publish) must confirm them.
