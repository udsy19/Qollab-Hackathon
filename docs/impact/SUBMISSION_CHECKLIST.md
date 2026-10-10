# Track 1 (Quantum Impact) — submission checklist

Deadline: **2026-10-11 19:00 ET**. Each line says who does it. Requirements come from `.claude/rules/hackathon-eligibility.md` and `vault/Research/qollab-platform-and-submission.md`; the submission form's own fields are NOT known (they are behind the owner's login) and are not invented here.

## Repo side (agents / overseer)

- [x] `impact-qollab/` integrated on `main`, runs locally: `cd impact-qollab && python -c "from main import main; main()"` exits 0 and sends exactly one backend job.
- [x] `node scripts/gates/qollab-submission.mjs impact-qollab` passes every rule except the YouTube link (which only exists after recording).
- [x] Project page (`impact-qollab/README.md`) final: run steps, verdict from the real run, limitations, prior-work disclosure, arXiv:2504.07844 credited as beam-angle optimisation (structure only), verbatim attribution "This effort is supported by Qollab & IonQ".
- [x] `docs/impact/FINAL_RESEARCH_REPORT.md`, `BENCHMARK_RESULTS.md`, `INTEGRATION_AUDIT.md` written from actual runs.

## Owner only

1. **Rotate the Alpaca paper key pair** (the runbook says it was disclosed). Only then, optionally, run the read-only data download in your own terminal (done 2026-10-10 by the overseer with the keys you supplied; `bash scripts/fetch_real_data.sh full` from `impact/`). The Qollab project does not need it.
2. **Prior-work line:** done — the page states QC-TRADE was developed with AI assistance on 2026-10-10 (owner, 2026-10-10). Only re-check if anything in it predates 2026-10-09 19:00 ET.
3. **Push** `main` to GitHub when you authorise it (agents and the overseer do not push).
4. **Create the Qollab project:** New Project → Upload your own files → the `impact-qollab/` folder (Qollab strips a single wrapping folder). Title, ≤240-char description and tags: `docs/impact/page-and-video.md` §1. Add the GitHub repo link. Check the write-up in Preview (YouTube embed, line breaks, KaTeX).
5. **Run it on Qollab:** Run on Qollab → Built-in simulator (24q) → Run, in Chrome/Edge/Brave/Opera (not Safari). Confirm the output matches the local run.
6. **IonQ simulator:** open Select QPU signed in. If an IonQ simulator says **Free**, run once (one job per run). If it says **Credits apply**, do not run it (your rule: free simulators only) and tell me, so the page does not claim an IonQ run.
7. **Record the demo video** (2:00–2:45) from `docs/impact/page-and-video.md` §2, upload to YouTube (Unlisted or Public), and send me the link; it goes into the README and the checker then passes fully.
8. **Publish** a public, default version (v1.0), then open the page signed out and check the write-up shows.
9. **Submit** from the registration page as captain, under the Quantum Impact theme, before 2026-10-11 19:00 ET. Note which fields the form asks for so the other tracks can prepare.
