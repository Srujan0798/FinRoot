# Report wave-7/08 — Streaming Reasoning Trace in UI

## Result
DONE

## What I built
- `src/interface/ui/components/trace.py` (UPDATE — added streaming effect)
- `src/interface/ui/components/chat.py` (UPDATE — trigger streaming on submit)

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src:. python3 -c "import interface.ui.components.trace; print('trace import OK')"
trace import OK

$ PYTHONPATH=src:. python3 -c "import interface.ui.components.chat; print('chat import OK')"
chat import OK

$ ruff check src/interface/ui/components/trace.py src/interface/ui/components/chat.py
All checks passed!
```

## Tests
- 13 tests added in `tests/unit/test_components.py` · 13 passed · 100% pass rate

## Decisions / deviations
- Kept non-streaming `render(state)` as fallback for harness tab and direct access
- Used `st.status()` context manager for the overall "Thinking..." container
- Added CSS animations for fade-in and flash effects
- Used `st.empty()` with 0.3s delays between trace steps
- Critic verdict appears last with flash effect (no separate empty placeholder)

## Surprises / gotchas
- N/A

## Follow-ups (for orchestrator triage — do NOT build now)
- Consider adding a toggle to enable/disable streaming for performance-critical scenarios
- Add option to adjust streaming delay based on network conditions
- Implement progress indicators for long-running traces

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)