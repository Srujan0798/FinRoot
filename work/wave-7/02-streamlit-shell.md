# Task wave-7/02 — Streamlit App Shell + Dark Finance Theme

> Read `work/WORKER_PROMPT.md` then build. DEMO-CRITICAL. Depends on W1 (done).

## Objective
The Streamlit app entry point with a polished dark finance theme and a 4-tab layout. Must load and
render without errors even before the component tasks (03/04/05) land (wrap their imports in try/except).

## Writes (ONLY these)
- `src/interface/ui/__init__.py`
- `src/interface/ui/app.py`
- `src/interface/ui/theme.py`

## Forbid
`src/interface/ui/components/**` (tasks 03/04/05 own those — import defensively).
`src/interface/cli/**`, `src/interface/core.py` (task 01 — import only).

## Contract
Read `.specify/specs/wave-7/contracts/ui.contract.md` § Streamlit UI.

## Steps
1. `theme.py` — dark finance palette + `apply_theme()`:
   - Deep charcoal/navy background (#0B0E14 / #11151C), card surfaces (#161B22), green (#3FB950) up / red (#F85149) down, muted text (#8B949E), accent (#58A6FF). Monospace for numbers.
   - Returns CSS string injected via `st.markdown(..., unsafe_allow_html=True)`.
   - A `confidence_badge(label)` and `risk_badge(band)` helper returning colored HTML chips.
2. `app.py`:
   - `st.set_page_config(page_title="FinRoot — Sovereign Financial Reasoning", layout="wide", page_icon="🌱")`
   - Apply theme. Sidebar: Mock-mode toggle (default ON), user/twin selector, a short "what is this" blurb.
   - 4 tabs: **💬 Chat**, **🧠 Reasoning Trace**, **👤 Digital Twin**, **📊 Harness**.
   - Each tab: `try: from interface.ui.components.<x> import render; render(...)` `except Exception as e: st.info("Component loading…: <reason>")` — never crash the app (FM-11: show the reason, don't silently pass).
   - Header with the FinRoot tagline + a one-line value prop.
   - `main()` function; `if __name__ == "__main__": main()`.
3. No tests required (Streamlit UI) but `app.py` must be import-safe: `python3 -c "import interface.ui.app"` works with PYTHONPATH=src.

## Acceptance
```bash
PYTHONPATH=src python3 -c "import interface.ui.app; import interface.ui.theme; print('UI shell imports OK')"
ruff check src/interface/ui/app.py src/interface/ui/theme.py src/interface/ui/__init__.py
# If streamlit installed: streamlit run src/interface/ui/app.py (loads, 4 tabs, dark theme)
```

## Report
`work/reports/wave-7/02-streamlit-shell.report.md`
