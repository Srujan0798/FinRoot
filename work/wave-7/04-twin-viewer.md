# Task wave-7/04 — Digital Twin + Portfolio Viewer Component

> Read `work/WORKER_PROMPT.md` then build. Depends on W2 (DigitalTwin, done).

## Objective
A Streamlit component that visualizes the user's Financial Digital Twin: profile (risk/horizon/income),
goals/constraints, and the portfolio holdings with allocation breakdown.

## Writes (ONLY these)
- `src/interface/ui/components/twin.py`

## Forbid
`components/chat.py`, `components/trace.py`, `components/harness.py`, `components/__init__.py`
(other tasks own those — do NOT create `__init__.py`, task 03 owns it).
`app.py`, `theme.py`, `core.py`.

## Contract
Read `.specify/specs/wave-7/contracts/ui.contract.md`. Twin shape from `data/samples/twin_profiles.json`
and `src/finroot/memory/digital_twin.py`.

## Steps
1. `render(twin: dict | None = None)`:
   - If `twin` is None, load the first profile from `data/samples/twin_profiles.json`.
   - Profile card: name, age, risk_tolerance (badge), investment_horizon, monthly income/expenses/surplus, tax bracket.
   - Goals + constraints as bulleted chips.
   - Holdings table: symbol, quantity, value, with a simple allocation bar (st.progress or a bar chart via st.bar_chart) showing % per holding.
   - Use `st.columns`, `st.metric` for the headline numbers (income, surplus, total holdings value).
   - Defensive: if data missing, show `st.info` with the reason (no crash, no silent pass).
2. Keep it self-contained: a module-level `load_demo_twin()` helper reading the JSON.
3. Importable standalone: guard streamlit import so the module imports even if streamlit absent (for ruff/CI), e.g. `try: import streamlit as st; except ImportError: st = None` and check in render.

## Acceptance
```bash
PYTHONPATH=src python3 -c "import interface.ui.components.twin as t; print('twin viewer imports OK'); print(t.load_demo_twin()['name'])"
ruff check src/interface/ui/components/twin.py
```

## Report
`work/reports/wave-7/04-twin-viewer.report.md`
