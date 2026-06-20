# Task wave-12/01 — Submission Message + Judge Quickstart

> Read `work/WORKER_PROMPT.md` then build. Pure docs. Depends on the shipped project.

## Objective
Two short, high-impact documents: (a) the message to send the SCALE ML Club organizers, and
(b) a one-page "run it in 30 seconds" quickstart for judges.

## Writes (ONLY these)
- `docs/SUBMISSION_MESSAGE.md`
- `docs/JUDGE_QUICKSTART.md`

## Forbid
README.md, docs/business/**, scripts/**, all other files.

## Context (read for real numbers — FM-12, do not invent)
- `results/metrics.json` (FRB headline: finroot mean, composite_lift_vs_rag_pct, n_tasks)
- `README.md` (positioning, judging-criteria map)
- repo URL: https://github.com/Srujan0798/FinRoot

## Steps
1. `docs/SUBMISSION_MESSAGE.md` — a ready-to-paste message to organizers:
   - 2-line what-it-is + the one-line pitch.
   - Repo link + how to run in 30s (docker one-liner AND mock CLI one-liner).
   - The 4-axis scorecard in one compact table (where each criterion is delivered).
   - The FRB headline number (read from metrics.json, stamp as_of_sha).
   - Links: demo video (placeholder `<your-video-link>`), screenshots dir, architecture diagram.
   - Tone: confident, concise, professional. ≤ 250 words.
2. `docs/JUDGE_QUICKSTART.md` — one page:
   - "Zero-key, offline" promise.
   - 3 copy-paste blocks: (a) `docker compose up` → open localhost:8501; (b) `pip install -e . && PYTHONPATH=src python -m interface.cli --mock "<query>"`; (c) `PYTHONPATH=src streamlit run src/interface/ui/app.py`.
   - 3 showcase queries to try (portfolio / tax with ₹ amount / the emergency-fund trap) and what to look for in each (reasoning trace, citation, prudence refusal).
   - Where the proof lives: `results/metrics.json`, `evals/reports/`, `docs/demo/`.

## Acceptance
```bash
test -f docs/SUBMISSION_MESSAGE.md && test -f docs/JUDGE_QUICKSTART.md && echo "files present"
grep -qi "github.com/Srujan0798/FinRoot" docs/SUBMISSION_MESSAGE.md && echo "repo link present"
grep -qiE "docker|streamlit|interface.cli" docs/JUDGE_QUICKSTART.md && echo "run steps present"
```
No fabricated numbers — pull from results/metrics.json (FM-12).

## Report
`work/reports/wave-12-final/01-submission-message.report.md`
