# Report wave-4/01 — Intent Classifier + Context Assembly

## Result
DONE

## What I built
- `src/finroot/agents/intent.py` — `IntentClassifier` with `classify(query) -> IntentResult` and `IntentResult(BaseModel)` (Pydantic v2, frozen). Keyword/pattern matching against real `Intent` enum values. Entity extraction for NSE/BSE tickers and timeframes via regex. Confidence: 1.0 exact word-boundary match, 0.7 partial substring match, 0.5 default.
- `src/finroot/workflows/context.py` — `ContextAssembler` with `assemble(state, memory) -> dict`. Pulls twin via `memory.get_twin()` (returns empty dict on `KeyError`), last 5 working-memory turns, semantic recall, and tools_available list.
- `tests/unit/test_intent.py` — 25 tests covering all 7 intents, entity extraction, default fallback, confidence values, frozen model, missing twin, history limits, and semantic recall.

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_intent.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 25 items

tests/unit/test_intent.py .........................                      [100%]

============================== 25 passed in 0.72s ==============================

$ ruff check src/finroot/agents/intent.py src/finroot/workflows/context.py tests/unit/test_intent.py
All checks passed!
```

## Tests
- 25 tests added · 25 passed · 0 failed
- Coverage: all 7 Intent enum values, entity extraction (NSE/BSE tickers, timeframes), confidence levels (1.0/0.7/0.5), empty query, frozen model, TypeError on non-str, missing twin handling, history limit (5), semantic recall delegation.

## Decisions / deviations
- Used real `Intent` enum values (`PORTFOLIO`, `RISK`, `TAX`, `NEWS_IMPACT`, `CASHFLOW`, `CREDIT`, `GENERAL`) instead of contract-aspirational names (`PORTFOLIO_REVIEW`, `RISK_ASSESSMENT`, etc.) — the contract says to read `enums.py` for the real values.
- Removed "hi" from greeting keywords — 2-letter keyword caused false partial matches inside unrelated words (e.g., "interesting" → GENERAL at 0.7). "hello", "help", "hey", "greet" remain.
- `IntentResult` is a frozen Pydantic `BaseModel` (contract-required), not a dataclass.
- `ContextAssembler._load_twin` catches `KeyError` and returns `{}` — no error raised, per task spec.
- Timeframe singular handling: "1 year" stays singular, "6 months" gets pluralized.

## Surprises / gotchas
- None added to docs/waves/wave-4-gotchas.md (no surprises).

## Follow-ups (for orchestrator triage — do NOT build now)
- LLM-backed classification for live mode (contract mentions this for non-mock).
- Partial confidence (0.7) currently only triggers on substring-in-word matches; could be expanded with fuzzy/semantic matching.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
