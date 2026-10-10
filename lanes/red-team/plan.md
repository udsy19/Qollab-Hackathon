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