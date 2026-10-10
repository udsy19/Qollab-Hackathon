
- 2026-10-10 consult 1: Story-ui modules must not depend on anything the platform lane owns. On Qollab, `<script>` in `index.html` does not run, `main.css` is the only stylesheet loaded, and JS cannot read project files (`vault/Research/qollab-platform-and-submission.md`). So:
- UI modules build their own DOM inside a root element passed in.
- Story data ships as JS modules, never JSON.
- All CSS lives in delimited sections of `echo/main.css`.
- Dev harnesses live outside `echo/` (`evidence/story-ui/harness/`) to stay under the 100-file cap.

`main.css` is a merge hot spot: merge ui-shell first, then the other workers rebase.

- 2026-10-10 consult 1: Until the quantum lane ships its §8.4 adapter, terminal work uses a harness stub with `engine: 'documented_preview'` that returns only textbook-exact values. The UI must always display the engine label. A screenshot without the label, or with stub values presented as Qiskit or backend output, is grounds to refuse the merge.
