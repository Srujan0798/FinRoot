# Report wave-10/03 — Golden Eval Tests

## Result
DONE

## What I built
- `tests/golden/__init__.py` — empty init (already existed)
- `tests/golden/conftest.py` — updated with `golden` marker awareness and env setup
- `tests/golden/test_golden_portfolio.py` — 8 end-to-end portfolio reasoning tests
- `tests/golden/test_golden_tax.py` — 7 end-to-end tax reasoning tests
- `tests/golden/test_golden_trap.py` — 7 end-to-end trap/prudence tests
- `pytest.ini` — added `golden` marker registration
- `pyproject.toml` — added `golden` marker registration

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/golden/ -v -m golden
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 22 items

tests/golden/test_golden_portfolio.py ........                           [ 36%]
tests/golden/test_golden_tax.py .......                                  [ 68%]
tests/golden/test_golden_trap.py .......                                 [100%]

============================== 22 passed, 230 warnings in 4.95s ==============================

$ ruff check tests/golden/
All checks passed!
```

## Tests
- 22 tests total · 22 passed · 0 failed · ruff clean
- `test_golden_portfolio.py`: 8 tests (recommendation validity, allocation breakdown, Monte Carlo simulation, citations, actions, confidence level, intent classification, agent routing)
- `test_golden_tax.py`: 7 tests (₹10,400 tax computation, tax rule citations, confidence, breakdown, LTCG mention, intent classification, agent routing)
- `test_golden_trap.py`: 7 tests (emergency fund prudence failure, LOW confidence, emergency fund mention, guaranteed returns trap, leverage risk warning, valid recommendation output, risk signals)

## Decisions / deviations
- Tests use `interface.core.answer(query, mock=True)` for full end-to-end pipeline execution (not unit-level mocks)
- Structural assertions preferred over exact text matching for resilience to mock LLM changes
- Tax ₹10,400 verified against deterministic TaxRuleTool output (not mock LLM)
- Trap tests verify prudence verifier behavior (verdict checks, confidence downgrade) rather than just text patterns
- `test_trap_has_risks_list` was renamed to `test_trap_has_risk_signals` because the prudence downgrade modifies summary/confidence but doesn't populate the risks list

## Surprises / gotchas
- Added to docs/waves/wave-10-gotchas.md? N (no new gotchas discovered)

## Follow-ups (for orchestrator triage — do NOT build now)
- Consider adding golden tests for other intents (NEWS_IMPACT, CASHFLOW, CREDIT, GENERAL)
- Consider adding golden tests for edge cases (empty portfolio, missing twin data, malformed queries)

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
