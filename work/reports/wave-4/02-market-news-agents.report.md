# Report wave-4/02 — MarketAnalystAgent + NewsInterpreterAgent

## Result
DONE

## What I built
- `src/finroot/agents/market_agent.py` — MarketAnalystAgent (ReAct, market_data + fundamental_analysis tools)
- `src/finroot/agents/news_agent.py` — NewsInterpreterAgent (ReAct, news_search + sentiment_analysis tools)
- `tests/unit/test_agents_market_news.py` — 16 tests covering both agents

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_agents_market_news.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 16 items

tests/unit/test_agents_market_news.py ................                   [100%]

============================== 16 passed in 1.09s ===============================

$ ruff check src/finroot/agents/market_agent.py src/finroot/agents/news_agent.py
All checks passed!
```

## Tests
- 16 tests · 16 passed · 0 failed
- MarketAnalystAgent: 8 tests (name, price output, fundamental output, multi-symbol, empty symbols, no intent, audit trail, mock source)
- NewsInterpreterAgent: 6 tests (name, news output, sentiment output, empty query, audit trail, articles present)
- Edge cases: 2 tests (preserve existing outputs, state.query fallback)

## Decisions / deviations
- Used `act()` (BaseAgent's abstract method) instead of task's `run()` — must match the base class interface
- Intent enum uses `NEWS_IMPACT`/`GENERAL`/etc. (not `MARKET_ANALYSIS` as contract suggests) — tests use actual enum values
- `_extract_symbols` searches intent_classifier → context_assembler → any output with "symbols" key (defensive fallback chain)
- NewsInterpreterAgent uses `_has_tool_output()` to track ReAct progress rather than a manual flag

## Surprises / gotchas
- N/A — no surprises encountered

## Follow-ups (for orchestrator triage — do NOT build now)
- Consider adding an `extract_query` method that uses the LLM for query extraction (currently keyword-based)

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
