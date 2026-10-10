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