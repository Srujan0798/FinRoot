# Report wave-4/05 — Plan-and-Execute Orchestrator (LangGraph)

## Result
DONE

## What I built
- `src/finroot/workflows/graph.py` — `build_graph()` returning a compiled LangGraph `StateGraph` with 5 nodes: `classify_intent`, `assemble_context`, `select_agents`, `execute_agents`, `synthesize`
- `src/finroot/agents/orchestrator.py` — `FinRootOrchestrator` (wires agents + graph + memory + audit) and `ResultSynthesizer` (builds `Recommendation` from tool outputs)
- `tests/integration/test_orchestrator.py` — 10 integration tests covering full pipeline, routing, audit, round-trip, and citation flows

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/integration/test_orchestrator.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False
collected 10 items

tests/integration/test_orchestrator.py ..........                        [100%]
======================= 10 passed, 110 warnings in 29.28s =======================

$ ruff check src/finroot/agents/orchestrator.py src/finroot/workflows/graph.py
All checks passed!
```

## Tests
- 10 tests added · 10 passed · 0 failed
- Tests cover: full pipeline for PORTFOLIO/TAX/NEWS_IMPACT intents, GENERAL (greeting) with no agents, audit trail entries, state round-trip, intent-to-agent routing, context assembly populates twin_snapshot, graph compilation, and citations in candidate

## Decisions / deviations
- **GraphState TypedDict instead of AgentState directly**: LangGraph's `get_type_hints()` cannot resolve the `AuditEvent` forward reference in `AgentState` (guarded by `TYPE_CHECKING`). Created `GraphState` TypedDict with `audit_events: list[Any]` and conversion functions `agent_state_to_graph`/`graph_state_to_agent` at the boundary.
- **Node renamed `plan` → `select_agents`**: LangGraph forbids node names that collide with state keys. `plan` is a state field (`list[str]`), so the node that populates it is named `select_agents`.
- **ResultSynthesizer embedded in orchestrator**: `workflows/synthesize.py` is Forbid for this task. A minimal `ResultSynthesizer` lives in `orchestrator.py` — it builds a `Recommendation` from tool outputs or returns a direct greeting for GENERAL intent.
- **Mock tools by default**: All sub-agents are instantiated with `mock=True` for tools that support it, ensuring deterministic offline behavior.

## Surprises / gotchas
- Added to `docs/waves/wave-4-gotchas.md`: Y (see below)

## Follow-ups (for orchestrator triage — do NOT build now)
- `ResultSynthesizer` should be moved to `workflows/synthesize.py` when that task lands (task 06?)
- Conditional edges by intent could optimize agent execution (skip unnecessary agents for some intents)
- Parallel agent execution (LangGraph `Send`) for independent sub-agents

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
