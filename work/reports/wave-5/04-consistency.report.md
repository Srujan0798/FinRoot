# Report wave-5/04 — Self-Consistency (N candidates → vote)

## Result
DONE

## What I built
- `src/finroot/reasoning/consistency.py` — `SelfConsistency` class + `ConsistencyResult` model
- `tests/unit/test_consistency.py` — 13 tests covering all required scenarios

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_consistency.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0,
         asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None,
         asyncio_default_test_loop_scope=function
collected 13 items

tests/unit/test_consistency.py .............                             [100%]

============================== 13 passed in 0.71s ==============================

$ ruff check src/finroot/reasoning/consistency.py
All checks passed!
```

## Tests
- `tests/unit/test_consistency.py` — 13 tests, 13 passed, 0 failed
  - `TestConsensusComputation` (7 tests): consensus logic with 0/1/2 dissenters, single candidate, 4-candidate tie
  - `TestCheckMethod` (4 tests): check() via mock generator, determinism, candidate count, missing-candidate error
  - `TestConsistencyResultModel` (2 tests): Pydantic ge/le constraints on agreement_score

## Decisions / deviations
- **agreement_score when all disagree**: When every candidate is unique (max group size = 1 and N > 1), agreement_score = 0.0 rather than 1/N. This is because the task spec explicitly lists `agreement_score=0.0` for the all-disagree case, and the formula "fraction that match the winner" would give 1/N which doesn't match the acceptance criteria.
- **Consensus comparison key**: Comparison uses `summary` text equality as the proxy for "same core recommendation". In mock mode, variants get different summary prefixes so they're distinct by design — the agreement check surfaces low consensus when wording changes produce different summaries.
- **Mock generation**: Deterministic rewording via prefixing ("", "Consider: ", "Looking at this differently: "). The 3 variants are always distinct, which exercises the full consensus pipeline.

## Surprises / gotchas
- None encountered beyond the agreement_score normalization decision above.

## Follow-ups (for orchestrator triage — do NOT build now)
- A fuzzy/semantic comparison (e.g., embedding similarity) could be more robust than exact summary matching for real LLM outputs where same meaning has different wording.
- The mock generator could support configurable modes (e.g., identical mode for testing "perfect agreement" through the full check() pipeline).

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
