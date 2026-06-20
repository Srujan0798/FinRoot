# Report wave-7/03 — Chat + Reasoning-Trace Panel

## Result
DONE

## What I built
- `src/interface/ui/components/__init__.py` — empty package marker
- `src/interface/ui/components/chat.py` — `render()` with `st.chat_input`, calls `interface.core.answer()`, renders finance card (summary, confidence badge, risk profile badge, actions, risks, alternatives, assumptions, citations), stores `AgentState` in `st.session_state["last_state"]`
- `src/interface/ui/components/trace.py` — `render(state=None)` reads state from arg or session, renders ordered timeline from `build_trace(state)`, self-critic 5-axis bars + pass/fail + must_fix, PrudentialVerifier verdict, citations table
- `tests/unit/test_components.py` — 11 tests covering imports, callable signatures, `build_trace` edge cases, and internal no-op helpers

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -c "import interface.ui.components.chat, interface.ui.components.trace; print('chat+trace import OK')"
chat+trace import OK

$ ruff check src/interface/ui/components/chat.py src/interface/ui/components/trace.py src/interface/ui/components/__init__.py
All checks passed!
```

## Tests
- `tests/unit/test_components.py` · 11/11 passed (see output below)

```
$ python3 -m pytest tests/unit/test_components.py -v
============================= test session starts ==============================
...
tests/unit/test_components.py ...........                                [100%]
============================== 11 passed in 0.85s ===============================
```

## Decisions / deviations
- The contract mentions `risk_band: RiskBand` on Recommendation but the actual `schemas/recommendation.py` has no `risk_band` field. I use the twin snapshot's `risk_tolerance` for the risk badge instead.
- Badge helpers (`confidence_badge`, `risk_badge`) are imported from `interface.ui.theme` as described in the contract.
- Internal render helpers (e.g. `_render_critic_verdict`) are public enough to be imported in tests; they no-op gracefully when their section is absent from state.

## Surprises / gotchas
- N

## Follow-ups (for orchestrator triage — do NOT build now)
- None

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
