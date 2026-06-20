# Task wave-7/08 — Streaming Reasoning Trace in UI

> Read `work/WORKER_PROMPT.md` then build. Makes the reasoning trace appear step-by-step.

## Objective
Make the Streamlit UI show reasoning steps appearing one-by-one (streaming effect) instead of all at once, creating a "live thinking" visual that impresses judges.

## Writes (ONLY these)
- `src/interface/ui/components/trace.py` (UPDATE — add streaming effect)
- `src/interface/ui/components/chat.py` (UPDATE — trigger streaming on submit)

## Forbid
`components/twin.py`, `components/harness.py`, `app.py`, `theme.py`, `core.py` (import only).

## Steps
1. Read existing `trace.py` and `chat.py` to understand current rendering.
2. Add streaming effect to `trace.py`:
   - `render_streaming(state)` — renders each reasoning step with a 0.3s delay using `st.empty()` + `time.sleep()`
   - Each step appears with a fade-in effect (CSS animation)
   - The critic verdict appears last with a "flash" effect
   - Use `st.status()` context manager for the overall "Thinking..." container
3. Update `chat.py`:
   - After calling `answer()`, call `render_streaming(state)` instead of `render(state)`
   - Show a spinner during the actual `answer()` call, then stream the trace
4. Keep non-streaming `render(state)` as fallback (for harness tab, direct access)
5. Guard: if streaming not desired (e.g., in tests), use `render(state)` directly

## Acceptance
```bash
PYTHONPATH=src:. python3 -c "import interface.ui.components.trace; print('trace import OK')"
ruff check src/interface/ui/components/trace.py src/interface/ui/components/chat.py
# Manual test: streamlit run src/interface/ui/app.py → ask a question → see steps appear one by one
```

## Report
`work/reports/wave-7/08-streaming-trace.report.md`
