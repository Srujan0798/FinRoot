# Report wave-3/02 — NewsSearchTool + SentimentAnalysisTool

## Result
DONE

## What I built
- `src/finroot/tools/news.py` — NewsSearchTool with mock (3 canned Indian market articles) and live (NewsAPI) modes
- `src/finroot/tools/sentiment.py` — SentimentAnalysisTool with keyword heuristic baseline and optional FinBERT path
- `tests/unit/test_tools_news.py` — 20 tests covering both tools

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_tools_news.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 20 items

tests/unit/test_tools_news.py ....................                       [100%]

============================== 20 passed in 8.10s ==============================

$ ruff check src/finroot/tools/news.py src/finroot/tools/sentiment.py
All checks passed!
```

## Tests
- 20 tests added · all passing
- News mock: 3 articles, shape validation, source/citation, max_results, env provider
- News live: raises ToolError without API key
- Sentiment: positive/negative/neutral keywords, empty text, whitespace, multiple texts
- Sentiment: model name, citation, FinBERT fallback, Pydantic validation, score clipping

## Decisions / deviations
- Used `urllib.request` for NewsAPI live calls (stdlib only, no `requests` dependency)
- Heuristic thresholds: score > 0.05 → positive, < -0.05 → negative, else neutral
- FinBERT lazy-loaded via module-level `_get_finbert_pipeline()` with singleton caching
- Empty/whitespace-only text returns neutral with score 0.0 (graceful handling)

## Surprises / gotchas
- N — no surprises encountered

## Follow-ups (for orchestrator triage — do NOT build now)
- Consider adding article deduplication for NewsAPI results
- FinBERT inference could be cached per-text for repeated calls

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
