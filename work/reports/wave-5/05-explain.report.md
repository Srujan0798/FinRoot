# Report wave-5/05 — Explainability Assembly

## Result
DONE

## What I built
- `src/finroot/reasoning/explain.py` — `ExplainabilityAssembly` with `assemble(state) -> dict`
- `tests/unit/test_explain.py` — 26 tests covering all contract requirements

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_explain.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 26 items

tests/unit/test_explain.py ..........................                    [100%]

============================== 26 passed in 0.18s ==============================

$ ruff check src/finroot/reasoning/explain.py
All checks passed!
```

## Tests
- 26 tests in `tests/unit/test_explain.py` — all pass
- Coverage: all 5 contract fields (reasoning_chain, risk_summary, confidence_breakdown, citations, principles_check)
- Parametrized boundary tests for confidence label thresholds (7 parametrized cases)

## Decisions / deviations
- `_build_confidence_breakdown()` maps critic overall >= 0.7 → HIGH, >= 0.4 → MEDIUM, else LOW (per contract §5, not the `THRESHOLD` from SelfCritic which is 0.6). This is intentional — the explain layer uses its own display-oriented thresholds.
- `_build_principles_check()` returns `compliant: True` with `warnings: ["not checked"]` when verifier hasn't run (the task spec says "default 'not checked'").
- `_build_risk_summary()` scans tool output string representations for "risk" substring (case-insensitive); caps at 5 items to keep the trace concise.

## Surprises / gotchas
- None. All interfaces matched the contract exactly.

## Follow-ups (for orchestrator triage — do NOT build now)
- None.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
