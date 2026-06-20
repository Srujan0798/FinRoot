# Task wave-6/05 — Eval Report Generator (metrics.json → markdown + delta)

> Read `work/WORKER_PROMPT.md` then build. Depends on W6-04 (harness/metrics.json).

## Objective
Turn `results/metrics.json` into a human-readable benchmark report (the artifact judges read), with
the headline lift vs baselines, per-domain breakdown, and the pass@k/pass^k table.

## Writes (ONLY these)
- `src/finroot/evaluation/report.py`
- `tests/unit/test_eval_report.py`
- `evals/reports/.gitkeep`

## Forbid
`harness.py`, `baselines.py`, `evals/graders/**`, `data/gold/**`.

## Contract
Read `.specify/specs/wave-6/contracts/evals.contract.md` § report.py + metrics.json shape.

## Steps
1. `report.py`:
   - `generate_report(metrics_path="results/metrics.json") -> str` (markdown).
   - Sections: headline (composite lift vs RAG %), system comparison table (pass@1/pass@k/pass^k/mean), per-domain breakdown table, methodology note (k trials, n tasks, mock), `as_of_sha` stamp.
   - `write_report(out_dir="evals/reports") -> Path` — writes `evals/reports/frb_report_<sha>.md` and a stable `evals/reports/latest.md`.
   - Fail loud if metrics.json missing (FM-11) with a clear "run scripts/run_evals.py first" message.
   - All numbers READ from metrics.json — never recompute/hand-type (FM-05/12).
2. `tests/unit/test_eval_report.py` (min 8): generate_report from a fixture metrics dict produces markdown containing the lift %, the system table, per-domain rows; missing file raises with helpful message; write_report creates the files.

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_eval_report.py -v
ruff check src/finroot/evaluation/report.py
# integration (if metrics.json exists from W6-04):
PYTHONPATH=src python3 -c "from finroot.evaluation.report import generate_report; print(generate_report()[:500])" 2>/dev/null || echo "(metrics.json not yet generated — unit tests cover it)"
```

## Report
`work/reports/wave-6/05-report-generator.report.md`
