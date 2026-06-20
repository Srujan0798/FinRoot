# Report wave-6/03 — Baselines (Naive RAG + Single-Agent)

## Result
DONE

## What I built
- `src/finroot/evaluation/baselines.py` — `NaiveRAGBaseline` and `SingleAgentBaseline`
- `tests/unit/test_baselines.py` — 25 tests

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_baselines.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini
collected 25 items

tests/unit/test_baselines.py .........................                   [100%]

============================== 25 passed in 0.30s ==============================

$ ruff check src/finroot/evaluation/baselines.py tests/unit/test_baselines.py
All checks passed!
```

## Tests
- 25 tests in 3 test classes + 1 shared-provider class
- 0 failures, 0 errors, 0 warnings
- Covers: AgentState return type, plan populated, deterministic (same query same answer), twin=None handling, twin provided, no citations for RAG, has citations for SingleAgent, has tool_outputs for SingleAgent, no tool_outputs for RAG, no risk framing for RAG, cross-baseline comparisons, shared MockProvider consistency

## Decisions / deviations
- Both baselines use `MockProvider` as the default LLM (deterministic, no network).
- `NaiveRAGBaseline`: single LLM call with query+optional context; no citations, no risk framing, no tool outputs — matches "typical RAG chatbot" description.
- `SingleAgentBaseline`: ReAct-like (plan -> call tool -> synthesize); has a simulated `mock_tool` call and one citation from it; no critic, no multi-agent orchestration, no principles.
- `_map_confidence` extracted as a module-level helper to avoid duplication.
- Neither baseline "sandbags" — they just lack the critic/principles/orchestration layers. The SingleAgent gets tool output and citations, making it better than NaiveRAG but worse than full FinRoot.

## Surfaces / gotchas
- N/A

## Follow-ups (for orchestrator triage)
- None from this task.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
