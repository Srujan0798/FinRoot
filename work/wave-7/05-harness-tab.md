# Task wave-7/05 — Live Harness Tab (run FRB in-app)

> Read `work/WORKER_PROMPT.md` then build. Depends on W6 (eval harness).

## Objective
A Streamlit tab that runs (or loads) the FRB benchmark and shows the FinRoot-vs-baselines lift live —
turning the 35% claim into something judges watch happen.

## Writes (ONLY these)
- `src/interface/ui/components/harness.py`

## Forbid
Other `components/**`, `app.py`, `theme.py`, `core.py` (import only). Do NOT create `components/__init__.py` (task 03 owns it).

## Contract
Read `.specify/specs/wave-7/contracts/ui.contract.md` and `.specify/specs/wave-6/contracts/evals.contract.md` (metrics.json shape).

## Steps
1. `render()`:
   - "Run benchmark" button → calls `finroot.evaluation.harness.run_harness(HarnessConfig(mock=True, k=3))` (wrap in spinner). Degrade gracefully if harness not importable → show `st.info`.
   - Prefer loading `results/metrics.json` if present (fast); offer a "re-run" button.
   - Headline metric: `composite_lift_vs_rag_pct` as a big `st.metric` with delta.
   - System comparison table: finroot / rag / single_agent → pass@1, pass@k, pass^k, mean_score.
   - Per-domain bar chart (st.bar_chart) of finroot mean scores.
   - A short caption: "k trials, n tasks, Mock mode — reproducible offline."
   - All numbers from metrics.json / harness result — never hard-coded (FM-05/12).
2. Import-safe with streamlit absent (guard import).

## Acceptance
```bash
PYTHONPATH=src python3 -c "import interface.ui.components.harness; print('harness tab import OK')"
ruff check src/interface/ui/components/harness.py
```

## Report
`work/reports/wave-7/05-harness-tab.report.md`
