# Report wave-4/06 — Result Synthesizer

## Result
DONE

## What I built
- `src/finroot/workflows/synthesize.py` — `ResultSynthesizer` class with `synthesize(AgentState) -> Recommendation`
- `tests/unit/test_synthesize.py` — 13 unit tests covering confidence logic, citations, risk flags, reasoning steps, edge cases, and JSON round-trip

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_synthesize.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 13 items

tests/unit/test_synthesize.py .............                              [100%]

============================== 13 passed in 1.27s ==============================

$ ruff check src/finroot/workflows/synthesize.py
All checks passed!

$ PYTHONPATH=src python3 -c "from finroot.workflows.synthesize import ResultSynthesizer; print('import OK')"
import OK
```

## Tests
- 13 tests added · 13/13 pass · coverage: confidence (HIGH/MEDIUM/LOW all paths), citation extraction, risk flag extraction, reasoning steps, errors noted in analysis, JSON round-trip, summary content, edge cases (0 outputs, all errors, no citations)

## Decisions / deviations
- **Interface:** Task spec says `synthesize(state: AgentState) -> AgentState`, but `graph.py:195` calls `synthesizer.synthesize(agent_st)` and uses the return directly as `Recommendation`. Made return type `Recommendation` to match the graph consumer. The result is equivalent — the caller sets `candidate`.
- **Citations in tool_outputs:** Some tool_output entries from `BaseAgent._call_tool` lack a `citations` key. The synthesizer handles both `Citation` objects and dicts, plus gracefully skips malformed entries with a warning log.
- **`_safe_add_citation`:** Uses a bare `except Exception` to skip malformed citation dicts. This is intentional — it logs a warning and continues rather than crashing the whole synthesis (the citations from other tools still survive). Per FM-11 the log is loud enough for audit.

## Surprises / gotchas
- No `.specify/specs/wave-4/contracts/graph.contract.md` file found (the .specify directory does not exist). Implemented from graph.py usage and the task brief instead.

## Follow-ups (for orchestrator triage — do NOT build now)
- Consider adding a `reasoning_steps` field to `Recommendation` (currently embedded in `analysis` as markdown text). Would make structured introspection easier.
- The `_safe_add_citation` fallback path could be tightened to require explicit fields rather than accepting partial dicts.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
