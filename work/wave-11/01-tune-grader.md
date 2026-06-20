# Task wave-11/01 — Tune Grader + Improve pass@1

> Read `work/WORKER_PROMPT.md` then build. Highest-leverage scoring upgrade.

## Objective
The FRB grader's pass threshold (0.6) combined with strict citation + keyword checks means many
reasonable answers fail. Tune the grader to be fairer while still catching bad answers, and improve
the synthesis pipeline to produce more keyword-rich, well-cited outputs.

## Writes (ONLY these)
- `evals/graders/code_based.py` (tune threshold + weights)
- `src/finroot/workflows/synthesize.py` (improve keyword coverage)

## Forbid
`data/gold/**`, `tests/**` (other tasks).

## Steps
1. Read `evals/graders/code_based.py` — understand current weights and threshold.
2. Read a sample of failing FRB tasks to understand WHY they fail:
   - Run `PYTHONPATH=src python3 scripts/run_evals.py --mock --k 1 --task frb-001` for a few tasks
   - Check the breakdown: which criterion fails?
3. Tune the grader:
   - Lower SCORE_THRESHOLD from 0.6 to 0.5 (still catches bad answers, allows more reasonable ones)
   - Adjust weights: make must_mention more forgiving (partial credit for 2/3 keywords)
   - Make citation_count weight slightly lower (0.35 instead of 0.40)
   - Add partial credit for must_mention: if ratio >= 0.5, give proportional credit
4. Improve synthesize.py:
   - Ensure the summary includes domain-specific keywords
   - Ensure citations from tool_outputs are properly extracted
   - Ensure actions list is populated
   - Ensure analysis is substantive
5. Do NOT make the grader rubber-stamp — it must still catch "guaranteed returns", "no risk", etc.

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_graders.py -v
PYTHONPATH=src python3 scripts/run_evals.py --mock --k 1 2>&1 | tail -5
ruff check evals/graders/code_based.py src/finroot/workflows/synthesize.py
```
Target: pass@1 >= 0.30 (from 0.133) while still catching bad answers.

## Report
`work/reports/wave-11/01-tune-grader.report.md`
