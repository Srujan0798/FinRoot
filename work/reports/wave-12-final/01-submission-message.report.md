# Report wave-12/01 — Submission Message + Judge Quickstart

## Result
DONE

## What I built
- `docs/SUBMISSION_MESSAGE.md` — ready-to-paste message for SCALE ML Club organizers (≤250 words, 4-axis scorecard, FRB headline, repo link, demo links)
- `docs/JUDGE_QUICKSTART.md` — one-page quickstart with 3 copy-paste run blocks, 3 showcase queries, proof locations

## Acceptance evidence (real output, this session)
```
$ test -f docs/SUBMISSION_MESSAGE.md && test -f docs/JUDGE_QUICKSTART.md && echo "files present"
files present

$ grep -qi "github.com/Srujan0798/FinRoot" docs/SUBMISSION_MESSAGE.md && echo "repo link present"
repo link present

$ grep -qiE "docker|streamlit|interface.cli" docs/JUDGE_QUICKSTART.md && echo "run steps present"
run steps present
```

## Tests
- Pure docs task; no code to test. Both files created and acceptance checks pass.

## Decisions / deviations
- Used real numbers from `results/metrics.json` (FM-12): finroot mean_score 0.7779, composite_lift_vs_rag_pct 128.4581, n_tasks 83, as_of_sha a335c45.
- Structured the submission message as a single self-contained paste block with scorecard table matching README.md's 4-axis breakdown.
- Judge quickstart uses three showcase queries covering portfolio (rebalance), tax (Section 80C with ₹), and the emergency-fund trap (prudence refusal) as specified.
- Repo URL set to https://github.com/Srujan0798/FinRoot per task brief.

## Surprises / gotchas
- No surprises encountered. N/A for gotchas file.

## Follow-ups (for orchestrator triage — do NOT build now)
- Replace `<your-video-link>` placeholder in SUBMISSION_MESSAGE.md once demo video is recorded.
- Consider adding a copy-paste version of the submission message without markdown tables (some chat platforms don't render tables).

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; metrics pulled from results/metrics.json (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (pure docs, no code)
- [x] No secrets committed (FM-07)
