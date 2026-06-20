# Task wave-7/03 — Chat + Reasoning-Trace Panel (the money shot)

> Read `work/WORKER_PROMPT.md` then build. DEMO-CRITICAL. Depends on W4 (done) + W5 reasoning.

## Objective
The two components that make FinRoot's reasoning VISIBLE to judges: a chat interface that calls
`answer()`, and a reasoning-trace panel that renders the step-by-step plan → tool calls → critic
verdict → citations. This is the centerpiece of the 35% story.

## Writes (ONLY these)
- `src/interface/ui/components/__init__.py`
- `src/interface/ui/components/chat.py`
- `src/interface/ui/components/trace.py`

## Forbid
`components/twin.py`, `components/harness.py` (other tasks). `app.py`, `theme.py`, `core.py` (import only).

## Contract
Read `.specify/specs/wave-7/contracts/ui.contract.md` (entry point, trace event shape, Recommendation).

## Steps
1. `components/__init__.py` — empty package marker (you own this file).
2. `chat.py` — `render()`:
   - `st.chat_input` for the query; keep history in `st.session_state`.
   - On submit: call `interface.core.answer(query, mock=<sidebar toggle>)`.
   - Render the answer as a finance card: summary, confidence badge, risk badge, action items, citations.
   - Store the returned AgentState in `st.session_state["last_state"]` so the Trace tab can read it.
   - Defensive: wrap the call; on error show `st.error` with the reason (no silent pass, FM-11).
3. `trace.py` — `render(state=None)`:
   - Read `state` or `st.session_state.get("last_state")`.
   - Render `interface.core.build_trace(state)` as an ordered, visually-stepped timeline: each step shows node, action, detail, source. Use `st.expander` per step or a styled list.
   - Show the Self-Critic verdict if present (`state.critique`): the 5 axis scores as small bars + overall + pass/fail + must_fix items.
   - Show the principles verifier verdict if present (`state.verifier_verdict`).
   - Show the citations table (claim → source → data).
   - If no state yet: `st.info("Ask a question in the Chat tab to see the reasoning trace.")`.
4. Import-safe with streamlit absent (guard import for ruff/CI).

## Acceptance
```bash
PYTHONPATH=src python3 -c "import interface.ui.components.chat, interface.ui.components.trace; print('chat+trace import OK')"
ruff check src/interface/ui/components/chat.py src/interface/ui/components/trace.py src/interface/ui/components/__init__.py
```

## Report
`work/reports/wave-7/03-chat-trace.report.md`
