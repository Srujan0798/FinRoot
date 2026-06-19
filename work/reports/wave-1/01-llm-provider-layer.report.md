# Report wave-1/01 — LLM Provider Layer

## Result
DONE

## What I built
- `src/finroot/llm/__init__.py` — public API re-exports
- `src/finroot/llm/base.py` — `LLMProvider` protocol, `LLMResult` model, `parse_reasoning_confidence()`
- `src/finroot/llm/mock.py` — deterministic offline provider (5 canned responses keyed by prompt hash)
- `src/finroot/llm/ollama.py` — thin Ollama adapter (lazy SDK import)
- `src/finroot/llm/groq.py` — thin Groq adapter (lazy SDK import, requires GROQ_API_KEY)
- `src/finroot/llm/openai.py` — thin OpenAI adapter (lazy SDK import, requires OPENAI_API_KEY)
- `src/finroot/llm/factory.py` — `get_provider()` factory (arg → env → default mock)
- `tests/unit/test_llm_provider.py` — 20 tests covering parser, mock, factory, credentials, protocol

## Acceptance evidence (real output, this session)
```
$ ruff check src/finroot/llm/
All checks passed!

$ PYTHONPATH=src python3 -c "from finroot.llm import get_provider; r=get_provider('mock').complete('hi'); print(r.provider, r.text[:20])"
mock Diversification acro

$ pytest tests/unit/test_llm_provider.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 20 items

tests/unit/test_llm_provider.py ....................                     [100%]

============================= 20 passed in 0.66s ==============================
```

## Tests
- 20 tests added · 20 passed · 0 failed
- Coverage: `parse_reasoning_confidence` (tags, no-tags, multiline, case-insensitive), `MockProvider` (determinism, tags always present, provider/model fields, type check), factory (default, string names, enum, unknown raises, env fallback), real providers (Groq/OpenAI raise without keys), protocol conformance, `LLMResult` extra-forbid

## Decisions / deviations
- GroqProvider/OpenAIProvider raise `RuntimeError` at `__init__` time when API key is missing (fail-loud per FM-11), not at `complete()` time. This surfaces the problem immediately rather than on first use.
- Ollama does not require a key to instantiate — it fails at `complete()` if the server is unreachable. This matches the sovereign-local-first design.
- Mock provider uses 5 canned responses rotated by SHA-256(prompt) % 5 to give variety while remaining deterministic.

## Surprises / gotchas
- `python` command not found on this system; `python3` required. Added to gotchas? N (system env issue, not a code surprise).

## Follow-ups (for orchestrator triage — do NOT build now)
- Streaming support for providers (SSE/async) — not in scope for wave-1.
- Retry/backoff logic for transient API failures — future wave concern.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
