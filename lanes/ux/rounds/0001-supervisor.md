=== PLAN ===
**Lane goal:** make both hackathon projects (Playground and Unlocked) look and feel great in the demo: visuals, plots, interaction flow and the 2–3 min demo narrative. This is judged only by before/after screenshots of the real project running on the Qollab path. The quantum logic is never changed.

**Where things stand (consult 1, 2026-10-10 00:49 UTC):** The repo holds only the org layer. Neither project lane has picked an idea, so there is no skeleton to present yet, and nothing on main or their integration branches to base work on.

**Approach:**
1. **Now (before ideas are picked):** find out how Qollab actually shows output to a judge who presses Run. That means notebook or script, inline matplotlib, interactive widgets, animations/GIF/HTML, image size limits, dark or light theme, and how long the IonQ simulator takes to answer, which shapes the demo pacing. Without this, every presentation choice is a guess. The finding is written to `vault/Research/` and shared with every lane.
2. **When the research lands:** commission a short presentation style note in `vault/Design/`. It covers palette, typography in plots, Qiskit visualisation conventions, and a "first 10 seconds after Run" principle. It is derived from what Qollab can actually render. Design only, no code in `playground/` or `unlocked/`.
3. **Once each project lane has a picked idea and a running skeleton:** for each project, one worker on a `lane/ux/<project>-visuals` branch based on that lane's integration branch. They take a before screenshot on the real run path, improve the visuals, take an after screenshot, and leave the quantum code untouched. A second worker drafts the demo narrative path (shot list against the real running project) and hands it to the deliverables lane.
4. Merge into `lane/ux/integration` only with before/after evidence. The project-lane supervisors pull it in.

**Done:** nothing yet.

**Next:** dispatch `qollab-render-research`.

**Risks:**
- Other lanes may research Qollab's runtime in parallel. The worker must read `vault/Research/` first and extend rather than duplicate.
- Ideas could be picked late, which compresses the ux window. Mitigation: the style note is ready beforehand, so visuals work can start the hour a skeleton exists.
- Qollab may render only static output. If so, polish moves to static figures and the demo video.
=== END PLAN ===

=== AGENT name=qollab-render-research model=sonnet base=lane/ux/integration ===
**GOAL:** Know exactly what a hackathon judge sees on Qollab after pressing Run, so that every presentation decision in this lane is built on fact, not guesswork.

**VISION:** Both projects should win on looks and clarity in the first seconds after Run, and in a 2–3 min demo video. That is only possible if we design for what Qollab can actually display.

**WHAT WE ARE BUILDING:** Two Qiskit projects for the Qollab x IonQ hackathon. Playground is playful or artistic; Unlocked makes a hard quantum idea click. Both are published on Qollab and run on its free simulators, including IonQ's. Ideas are not picked yet. Your output feeds the ux lane (presentation) and every other lane.

**WHAT HAS NOT WORKED:** Nothing has been tried yet; this is the first build. Org-wide failures to avoid:
- judging the wrong artifact
- making claims without evidence
- doing meta-work instead of product work

How Qollab runs projects is recorded nowhere yet. Another lane may be researching it right now.

**Vault notes to read first:**
- `vault/AGENTS.md`, `vault/Home.md`
- `vault/Index.md`
- `vault/Missions/qollab-ionq-hackathon-2026.md`
- `vault/Design/lanes-and-supervisors.md` (§ "Where research findings go")
- **everything under `vault/Research/`**. If another lane has already written a Qollab runtime note, EXTEND that note with a presentation section rather than writing a second one, and say so in your report.

**Questions to answer, each with a source URL or a screenshot:**
1. Project format on Qollab: Jupyter notebook, Python script, or something else? What happens visually when a judge presses Run?
2. Output rendering:
   - inline matplotlib (static PNG? `%matplotlib widget`?)
   - Qiskit's own visualisations (`circuit.draw('mpl')`, `plot_histogram`, `plot_bloch_multivector`, `plot_state_qsphere`)
   - ipywidgets and sliders
   - matplotlib animations, HTML/JS output, GIF/video embeds
   - plotly
   - which of these render, and which are blank or blocked?
3. Theme: is the background dark or light, and how wide is the output cell? What does that imply for figure size and colours?
4. IonQ simulator on Qollab: how jobs are submitted, typical wait time, and shot limits. These shape the demo pacing.
5. Available packages: preinstalled versions of qiskit, matplotlib and others. Can extra packages be pip-installed? Network limits?
6. Project page: what it can contain (images, GIFs, embedded video, markdown).

**Where to start:**
- qollab.xyz: its FAQ, the hackathon page, and the lessons "Programming your first quantum circuits".
- Published example projects on Qollab: screenshot one or two showing rendered output, if this is possible without sign-in.
- Never create accounts, never sign in, never spend money.

**Deliver:**
- `vault/Research/qollab-presentation-capabilities.md` (or a section in an existing Qollab runtime note), with sources and a "what this means for presentation" list of 5–10 concrete do/don't lines.
- Any screenshots under `renders/ux/qollab-research/`.
- Hub regenerated with `node scripts/vault-hubs.mjs`.
- Committed on your branch.

Where a question cannot be answered without signing in, mark it **UNKNOWN — needs owner account** and stop. Do not guess.

**How I will judge it:**
- every capability claim carries a source link or a screenshot
- unknowns are named as unknowns
- the do/don't list is specific enough that a visuals worker can act on it without re-researching

**Report:** `reports/qollab-render-research.md`. It opens with a **Vault check** (notes read, what was known, what you reused, what is stale), then a TL;DR, findings, unknowns and the paths of the evidence. Write a checkpoint report within 1 h even if research is incomplete.
=== END AGENT ===

=== LEARN ===
The ux lane cannot start product work until a project lane has a picked idea and a running skeleton. Until then, the only non-speculative prep is to research what Qollab can render and to write a style note derived from that research. Do not write visuals code against an imagined project.
=== END LEARN ===
