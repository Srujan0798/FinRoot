# Report wave-2/02 — Semantic Memory (ChromaDB + JSON fallback)

## Result
DONE

## What I built
- `src/finroot/memory/semantic.py` — `SemanticMemory` class with lazy ChromaDB import and stdlib TF-IDF fallback
- `tests/unit/test_semantic_memory.py` — 22 tests covering both ChromaDB (mocked) and JSON fallback paths

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_semantic_memory.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 22 items

tests/unit/test_semantic_memory.py ......................                [100%]

============================== 22 passed in 2.12s ==============================

$ ruff check src/finroot/memory/semantic.py tests/unit/test_semantic_memory.py
All checks passed!
```

## Tests
- 22 tests added · 22 passed · 0 failed
- Coverage areas: add/search round-trip, delete, clear, k-limit, empty-search returns `[]`, ChromaDB path (mocked via monkeypatch), JSON fallback activated when chromadb absent, metadata preserved, helper functions (`_tokenize`, `_cosine_similarity`)

## Decisions / deviations
- `_JsonFallbackStore.add` accepts optional `doc_id` parameter so `SemanticMemory` can pass its own UUID through, ensuring `delete(doc_id)` works correctly on the fallback path
- ChromaDB distance-to-score conversion: `score = 1 - dist` (clamped to 0), since ChromaDB returns L2 distances by default
- TF-IDF IDF formula uses `log((N+1)/(df+1)) + 1` (smoothed) to avoid division-by-zero and negative values

## Surprises / gotchas
- Initial implementation had a bug where `SemanticMemory.add` returned a UUID that didn't match the one stored in the fallback (each generated independently). Fixed by threading the doc_id through to the fallback store. Added to docs/waves/wave-2-gotchas.md: N (minor, caught by tests before report)

## Follow-ups (for orchestrator triage — do NOT build now)
- ChromaDB distance metric could be configurable (cosine vs L2) via constructor param
- Fallback TF-IDF could use n-grams for better partial-match retrieval

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
