# Task wave-7/06 — Plotly Financial Charts in Streamlit UI

> Read `work/WORKER_PROMPT.md` then build. Upgrades the UI from basic st.bar_chart to rich Plotly visualizations.

## Objective
Replace basic Streamlit charts with interactive Plotly financial visualizations: candlestick charts, pie charts for allocation, time-series overlays, and gauge charts for confidence/risk.

## Writes (ONLY these)
- `src/interface/ui/components/charts.py` (NEW — reusable chart components)
- `src/interface/ui/components/twin.py` (UPDATE — use Plotly pie for allocation)
- `src/interface/ui/components/harness.py` (UPDATE — use Plotly bar chart for domain scores)
- `tests/unit/test_charts.py` (NEW)

## Forbid
`src/interface/ui/app.py`, `src/interface/ui/theme.py`, `components/chat.py`, `components/trace.py` (import only).

## Steps
1. `charts.py` — reusable Plotly chart builders:
   - `allocation_pie(holdings: list[dict]) -> go.Figure` — pie chart of portfolio allocation
   - `domain_bar_chart(scores: dict[str, float]) -> go.Figure` — horizontal bar chart for FRB domain scores
   - `confidence_gauge(score: float, label: str) -> go.Figure` — gauge chart for confidence
   - `risk_meter(risk_level: str) -> go.Figure` — visual risk indicator
   - All charts use the dark theme (transparent bg, green/red accents matching theme.py)
   - Lazy-import plotly: `try: import plotly.graph_objects as go; except ImportError: go = None`
2. Update `twin.py`: replace `st.bar_chart()` with `st.plotly_chart(allocation_pie(holdings))`
3. Update `harness.py`: replace `st.bar_chart()` with `st.plotly_chart(domain_bar_chart(scores))`
4. `tests/unit/test_charts.py` (min 6): each chart builder returns correct type, handles empty data gracefully
5. Guard all plotly imports so the app still works if plotly is not installed (st.info fallback)

## Acceptance
```bash
PYTHONPATH=src:. python3 -c "import interface.ui.components.charts; print('charts import OK')"
PYTHONPATH=src:. python3 -m pytest tests/unit/test_charts.py -v
ruff check src/interface/ui/components/charts.py
# If streamlit+plotly installed: streamlit run src/interface/ui/app.py (charts render)
```

## Report
`work/reports/wave-7/06-plotly-charts.report.md`
