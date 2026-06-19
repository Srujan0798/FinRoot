# Report wave-4/04 — TaxPlannerAgent

## Result
DONE

## What I built
- `src/finroot/agents/tax_agent.py` — TaxPlannerAgent (ReAct sub-agent, max 2 iterations)
- `tests/unit/test_agent_tax.py` — 14 tests covering tax computation, missing input, query parsing, profile integration, audit trail, and metadata

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_agent_tax.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 14 items

tests/unit/test_agent_tax.py ..............                              [100%]

============================= 14 passed in 15.12s ==============================

$ ruff check src/finroot/agents/tax_agent.py
All checks passed!
```

## Tests
- 14 tests: 3 tax computation (LTCG, STCG_EQUITY, STCG slab), 1 below-exemption edge, 4 missing/invalid input, 1 query parsing, 1 profile-tool integration, 1 audit trail, 3 agent metadata
- All pass, ruff clean

## Decisions / deviations
- Used `act()` (BaseAgent abstract method) rather than `run()` as described loosely in the brief.
- Agent reads annual_income from twin_snapshot first; falls back to calling UserProfileTool only if snapshot lacks income data. This matches the RiskAssessorAgent pattern and avoids requiring every test to have a valid profile.
- Query parsing extracts gain amount via regex (₹/Rs./INR prefix) and gain type via keyword matching.
- The contract `.specify/specs/wave-4/contracts/graph.contract.md` did not exist in the repo at dispatch time; implemented from the task's inline contract description + existing codebase patterns.

## Surprises / gotchas
- N/A — no surprises encountered.

## Follow-ups (for orchestrator triage — do NOT build now)
- None.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
