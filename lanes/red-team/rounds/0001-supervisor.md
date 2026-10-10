=== PLAN ===
**Lane:** red-team (reports only, no product edits). Plan row 7.

**Goal:** Three independent checks on ECHO: ONE OF ONE, each reported with evidence to the lane that owns the fix:
1. A physics audit of `CLAUDE_CODE_PROMPTS.md` Prompt 6 against the real quantum code and tests. It covers every claim, the four (m0,m1) bit pairs, Qiskit endianness, the one-`backend.run` limit and misleading labels.
2. Blind newcomer playtests of the newest integrated build in a local runner, recording where players get stuck and whether they can answer the three teach-back questions.
3. A score against the judging rubric (novelty, technical execution, impact, documentation), with evidence.

**Where things stand (T+~6h, 2026-10-10 03:19 UTC = 23:19 ET Fri):** `echo/` does not exist yet. There is no quantum code to audit and no build to playtest. G1 (quantum verified) is due Sat 04:00 ET and G2 (graybox playable) is due Sat 17:00 ET.

**Approach:** Build the independent ground truth before the code exists, so the audit can run within an hour of the quantum lane's code landing.
- Gate-independence law 3: write the check first.
- Law 5: the spec is a hypothesis too, so Prompt 6 and vision §7 are audited, not trusted.
- The oracle is derived from Qiskit and first principles, never from the quantum lane's code.

**Now:**
- `physics-oracle-audit`: an independent Qiskit oracle for teleportation. It covers all 4 bit pairs, both endianness conventions, no-cloning fidelity bounds and no-signalling via `partial_trace`. It also audits Prompt 6 and vision §7 line by line for physics errors and ambiguities. Findings go to `vault/Reports/`.
- `rubric-research`: fetch the Qollab hackathon terms and judging criteria and turn them into a rubric note with evidence descriptors in `vault/Research/`. This is the scoring frame for part 3.

**Next:**
- When `echo/quantum/` lands on any lane branch, dispatch `physics-code-audit`. It runs the oracle against the real code and tests, sabotages the code's tests on a disposable copy to check they go red, and checks labels in `echo/ui`/`echo/data`.
- When a G2 graybox build is integrated, dispatch 1–2 `blind-playtest` workers. Each gets its own port, plays title → ending through the real controls, and records screenshots and video, stuck points and teach-back answers.
- After the first playtest, dispatch `rubric-score`.
- Repeat the playtest after G3 and before freeze (Sun 14:00 ET), aiming for 3 consecutive full runs.

**Done:** nothing yet.

**Risks:**
- If the graybox is late, the playtests squeeze toward freeze. Mitigation: playtest any partial vertical slice as soon as it exists, and report it as PARTIAL.
- A worker might calibrate the oracle on the quantum lane's code (law 4). The brief forbids this.
- Claims about running on Qollab are only allowed when the owner confirms them; otherwise results say "local runner".
- Credit names have not been given, so any credits finding is raised as a question, not written.
=== END PLAN ===

=== AGENT name=physics-oracle-audit model=opus base=lane/red-team/integration ===
**GOAL:** When the quantum lane's code lands, the red-team can say within an hour, with an artifact, whether ECHO's quantum puzzles are physically true. That means the four teleportation bit pairs, the correction rule, endianness, no-cloning, no-signalling, the story token consumed once and at most one `backend.run`. Today, before that code exists, you build the independent ground truth. You also audit the spec itself, because a prescribed fix is a hypothesis (`.claude/rules/gate-independence.md` law 5) and the vision docs can be wrong.

**VISION:** Judges and first-time players must be taught true physics. A teleportation game that mislabels m0/m1, flips endianness, or implies faster-than-light signalling is worse than no game. "Truthful quantum" is a non-negotiable in `CLAUDE.md`.

**WHAT WE ARE BUILDING:** ECHO: ONE OF ONE, a Qollab-native Three.js game under `echo/` with local Pyodide Qiskit. The physics is normative in `ECHO_MASTER_VISION.md` §7 and §2.4. `CLAUDE_CODE_PROMPTS.md` Prompt 6 is the physics-audit prompt. Conventions: m0 = source readout, m1 = Alice's Bell half; the receiver applies X iff m1=1 and Z iff m0=1.

**WHAT HAS NOT WORKED:** Nothing on ECHO yet; this is a fresh start. Org-wide failures to avoid:
- Optimising against a test suite instead of the product.
- Judging the wrong artifact.
- Meta-work instead of product work. Your oracle must be something the code audit will actually run, not a document about one.

**Vault and docs to read first:**
- `vault/AGENTS.md`, `vault/Home.md`, `vault/Index.md`
- `vault/Missions/echo-hackathon-submission.md`
- `vault/Research/qollab-platform-and-submission.md` (Pyodide Python 3.14, Qiskit 2.x, the one-job limit, the callPromising/XHR finding)
- `vault/Design/gate-independence-cases.md` (laws 3, 4, 5, 15)
- Then `ECHO_MASTER_VISION.md` §2.4, §7, §9 and `CLAUDE_CODE_PROMPTS.md` Prompt 6 in full.

**Constraints:**
- Red-team edits no product files. Nothing goes under `echo/`.
- Your oracle lives under `evidence/red-team/physics-oracle/` with a README.
- Your report goes in `vault/Reports/`.
- Use the venv Python (qiskit 2.5, pytest). Use only Qiskit APIs that exist in Qiskit 2.x as shipped in Pyodide: `Statevector`, `DensityMatrix`, `partial_trace`, `state_fidelity`, plus basic circuit construction. Flag anything that needs Aer.
- **Do not read or calibrate against any `echo/quantum/` code**, even if it appears on a branch while you work (law 4). The oracle comes from first principles and Qiskit only.

**Deliver:**
1. **The oracle**, a runnable pytest file plus a small library under `evidence/red-team/physics-oracle/`. It must establish:
   - **Teleportation:** for random input states (seeded, at least 50) and for each of the 4 (m0,m1) outcomes, the post-measurement Bob state, the correct correction and fidelity 1 after correction. It must also show that every one of the other 3 wrong corrections fails, with the fidelity table printed.
   - **Endianness:** which classical bit index carries m0 vs m1 under Qiskit's little-endian bitstrings, with a worked bitstring → (m0,m1) table. Name the exact trap: a `counts` key `'01'` means c1=0 and c0=1.
   - **Consumption:** after Alice's Bell measurement her source qubit is in a computational basis state, so the original is no longer recoverable there. This is checked by fidelity against the input.
   - **No-cloning:** for the best universal symmetric cloner (or any cloning circuit the spec describes), the per-copy fidelity is ≤ 5/6 on average. A CNOT "cloner" works only on basis states and fails on |+>; give the numbers.
   - **No-signalling:** Bob's reduced density matrix (`partial_trace`) is identical, to 1e-12, whatever Alice measures or does, until classical bits arrive.
   - **Pyodide compatibility:** list the imports and confirm none need Aer or a compiled extension Pyodide lacks. If you cannot verify a point, say so.
2. **The law-3 demonstration:** sabotage the oracle and show it goes red. Swap the X/Z rule, swap m0/m1, reverse the bitstring and drop a correction, each on a disposable copy, and list which sabotage did NOT go red.
3. **The spec audit:** a table of every physics claim in vision §7 and §2.4 and in Prompt 6. Mark each TRUE, FALSE, AMBIGUOUS or UNTESTABLE-AS-WRITTEN, with the oracle line that settles it. Flag any wording a player could read as faster-than-light communication, cloning, "certified randomness" or matter teleportation.
4. **A code-audit checklist:** the exact steps the later `physics-code-audit` worker will run against `echo/quantum/`, `echo/tests/` and the UI labels, including how to count `backend.run` call sites and paths.

**How I will judge it:**
- I run your pytest myself, and it must pass.
- Your sabotage table must show red for each sabotage. A sabotage that stayed green and is reported as such counts in your favour.
- Every spec-audit row cites an oracle line or a doc line.
- Any FALSE or AMBIGUOUS row is written as a proposed change for the owner, not as an edit. The vision docs are owner-only.

**Report:** `lanes/red-team/reports/physics-oracle-audit.md` (copy the durable findings to `vault/Reports/` and run `node scripts/vault-hubs.mjs`).
- It opens with a **Vault check** (notes read, what was known, what you reused, what is stale).
- Then TL;DR, evidence (commands, exit codes, artifact paths), the nulls, `## Findings for owning lanes` and `## Questions for the owner`.
- Checkpoint within 1 h, even if partial (mark it PARTIAL).
- Commit to your branch.
=== END AGENT ===

=== AGENT name=rubric-research model=sonnet base=lane/red-team/integration ===
**GOAL:** Give the red-team a precise, sourced scoring frame, so that "score against the four-trait rubric" means what the Qollab × IonQ judges will actually weigh, not our guess.

**VISION:** ECHO wins only if judges see novelty, technical execution, impact and documentation. Our later rubric scores must predict what the judges see, and must point each owning lane at the cheapest gap to close before freeze (Sun 14:00 ET).

**WHAT WE ARE BUILDING:** ECHO: ONE OF ONE, a playable cyberpunk 3D puzzle game on Qollab that teaches no-cloning, no-signalling and teleportation with real local Qiskit (`echo/`, not yet built). Submission requirements: published on Qollab, MIT, a 2–3 min public demo video, and a write-up.

**WHAT HAS NOT WORKED:** Nothing on ECHO yet. Earlier-org lesson: the vision doc is not the source of truth over Qollab's own pages; fetch them.

**Read first:**
- `vault/AGENTS.md`, `vault/Index.md`
- `vault/Research/qollab-platform-and-submission.md`. Reuse it; do not redo it. Extend only what is missing.
- `ECHO_MASTER_VISION.md` §1.4, §12.5, §17
- `QOLLAB_DEPLOYMENT.md`
- Earlier-org reports (read-only): `/Users/udsy/agent-org-qollab-hackathon/lanes/*/reports/`

**Do:**
- Fetch https://qollab.xyz/programs/hackathon/terms and any linked judging, track or "Quantum Unlocked" pages.
- Extract the exact judging criteria, weights, tie-breaks, eligibility and submission requirements, quoting them verbatim with URLs and fetch dates.
- For each criterion, write 3–5 concrete, observable evidence descriptors for ECHO: what a judge would see on the project page, in the video or in play that scores high vs low.
- Note every place where Qollab's pages contradict our vision docs. Those are owner questions; do not edit the docs.

**Deliver:** `vault/Research/judging-rubric.md` (frontmatter as other Research notes, sourced, linked from the hub via `node scripts/vault-hubs.mjs`, and `python3 scripts/gen-subject-index.py`).

**How I will judge it:**
- Every criterion carries a verbatim quote and URL.
- Anything not found is said to be not found, not invented.
- The descriptors are things a tester can observe.

**Report:** `lanes/red-team/reports/rubric-research.md`.
- It opens with a **Vault check**.
- Then TL;DR, sources, contradictions, `## Questions for the owner`.
- Checkpoint within 1 h.
- No product edits.
=== END AGENT ===

=== LEARN ===
Consult 1 (Fri 23:19 ET): `echo/` does not exist yet, so a code audit or playtest now would audit nothing. The red-team's first move is to build an independent physics oracle and audit the spec before the code arrives (gate-independence laws 3 and 5). The rule against calibrating on the quantum lane's code (law 4) is written into every physics brief.
=== END LEARN ===
