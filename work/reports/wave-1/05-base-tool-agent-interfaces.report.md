# Report wave-1/05 — Base Tool & Agent Interfaces

## Result
DONE

## What I built
- `src/finroot/tools/__init__.py` — already existed with `BaseTool` re-export (unchanged)
- `src/finroot/tools/base.py` — `BaseTool(ABC, Generic[In, Out])` with TTL cache, token-bucket rate limiter, retry+exponential-backoff, audit-emit on success/failure, and `ToolCallError` for loud failure (never silent, no synthetic data)
- `src/finroot/agents/__init__.py` — new package init exporting `BaseAgent`
- `src/finroot/agents/base.py` — `BaseAgent(ABC)` with `LLMProvider` + `list[BaseTool]` + `AuditTrail`, abstract `act(state) -> state`, and `_call_tool` helper that dispatches to a named tool and records a `Citation`
- `tests/unit/test_base_interfaces.py` — 14 tests covering cache (hit, miss, expiry), rate limiting, loud failure propagation, audit emission on success and failure, agent tool dispatch, unknown tool rejection, and init requirements

## Acceptance evidence (real output, this session)
```
$ ruff check src/finroot/tools/base.py src/finroot/agents/base.py
All checks passed!
---EXIT: 0

$ pytest tests/unit/test_base_interfaces.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 14 items

tests/unit/test_base_interfaces.py ..............                        [100%]

============================== 14 passed in 2.37s ==============================
```

## Tests
- `tests/unit/test_base_interfaces.py` — 14 tests, all pass

## Decisions / deviations
- **BaseTool.audit is optional (`None`)**: tools can be used without an audit trail (e.g. test helpers). When absent, audit emission is a no-op.
- **Cache key = SHA-256 of `str(inp)`**: deterministic, fast, works for any hashable input. Different types producing the same string representation are treated as the same key (acceptable for base abstraction; concrete tools can override `_cache_key`).
- **Retry backoff**: `base_delay * 2^attempt` (standard exponential backoff). Default: 1s, 2s, 4s for max_retries=3.
- **BaseAgent.audit is required**: per the contract signature `__init__(self, llm, tools, audit)`.
- **No rate-limit key discrimination**: the token bucket is tool-wide (not per-input). This is the simplest correct default; concrete tools can override `_consume_token` for per-key rate limiting.

## Surprises / gotchas
- None. Everything went as specified.

## Follow-ups (for orchestrator triage — do NOT build now)
- None.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
