# Report wave-5/03 — Rooted Prudence Principles Verifier

## Result
DONE

## What I built
- `src/finroot/reasoning/principles.py` — `PrudentialVerifier` with 7 prudence checks and `PrudentialVerdict` Pydantic model
- `tests/unit/test_principles.py` — 20 tests covering all 7 principles plus edge cases

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_principles.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 20 items

tests/unit/test_principles.py ....................                       [100%]

============================== 20 passed in 0.61s ==============================

$ ruff check src/finroot/reasoning/principles.py
All checks passed!
```

## Tests
- 20 tests added · 20 passed · 0 failed
- Covers all 7 principles: emergency fund (2), diversification (2), risk match (2), no guarantees (3), tax awareness (2), horizon match (2), evidence (2), plus integration/verdict shape (3)

## Decisions / deviations
- **Guarantee negation handling**: "does not guarantee" is excluded from the no-guarantees check via a secondary negation pattern, since the contract intent is to flag *promises* of returns, not disclaimers.
- **Risk/horizon matching**: `twin_snapshot` fields `risk_tolerance` and `horizon` are read with lowercase normalization. Conservative = {"conservative", "low", "very_low"}; long horizon = {"long", "long_term", "10+ years", "retirement"}.
- **Diversification**: Uses regex to extract percentages from text. Any single allocation >40% triggers FAIL.
- **Evidence threshold**: `tool_outputs < 2` combined with numeric content in the recommendation triggers FAIL.
- **Critical vs warning**: Checks 1-4, 7 are critical (determine `compliant`); checks 5-6 are warnings only per contract.

## Surprises / gotchas
- N/A — no surprises encountered.

## Follow-ups (for orchestrator triage — do NOT build now)
- Consider making `_extract_text` also scan `state.final` if `candidate` is None but `final` exists (currently handled but edge case worth testing).
- The guarantee negation regex could miss edge cases like "I can't guarantee" — could add `can't\s+guarantee` to negation pattern if needed.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
