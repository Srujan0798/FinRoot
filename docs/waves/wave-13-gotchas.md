# Wave 13 — Gotchas

## 02 — Hosted Demo Link

1. **No `.specify/specs/wave-13/contracts/` directory.**
   The task references `.specify/specs/wave-13/contracts/` but the directory does not exist.
   This is consistent with wave-12-final (same observation). Not a blocker.

2. **`requirements.txt` triggers ruff `invalid-syntax` errors.**
   Ruff ~0.5 attempts to parse `requirements.txt` as Python when the file is passed directly.
   Comma-separated version specifiers like `langchain>=0.3,<0.4` are valid PEP 508 pip syntax
   but not valid Python. Workaround: only run `ruff check` on `.py` files, or add
   `requirements.txt` to `[tool.ruff].exclude`.

3. **`streamlit_app.py` emits warnings on import outside Streamlit runtime.**
   `st.set_page_config()` called at module level produces "missing ScriptRunContext" warnings
   when the file is imported (not run via `streamlit run`). These are harmless — Streamlit
   >=1.36 does not raise. The acceptance command confirms import succeeds.

4. **`langgraph` has no `__version__` attribute.**
   Unlike most packages, `langgraph` (v0.2.76) does not expose `__version__`.
   Version check via `pip show langgraph` works instead.
