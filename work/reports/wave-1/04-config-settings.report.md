# Report wave-1/04 — Config, Settings & Prompt Registry

## Result
DONE

## What I built
- `config/__init__.py` — package init exporting `Settings`, `get_settings`, `PromptRegistry`
- `config/settings.py` — `Settings` (pydantic-settings, `FINROOT_*` env prefix, sane defaults) + `get_settings()` cached via `lru_cache`
- `config/prompts.py` — `PromptRegistry` with versioned prompts, `get(name, version="latest")`, error on unknown name/version (FM-11)
- `src/finroot/utils/__init__.py` — package init (was `.gitkeep`)
- `src/finroot/utils/config.py` — `assert_settings()` (validates critical params, fails loud) + `print_startup_banner()` (one-line active config)
- `tests/unit/test_config.py` — 24 tests covering defaults, env overrides, caching, registry, and assertion/banner utils

## Acceptance evidence (real output, this session)
```
$ ruff check src/finroot/utils/ config/
All checks passed!

$ PYTHONPATH=src FINROOT_LLM_PROVIDER=ollama python3 -c "from config.settings import get_settings; print(get_settings().llm_provider)"
Provider.OLLAMA

$ python3 -m pytest tests/unit/test_config.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, anyio-4.13.0
collected 24 items

tests/unit/test_config.py ........................                       [100%]

============================== 24 passed in 0.30s ==============================
```

**Note on acceptance command:** The task's spec command `FINROOT_LLM_PROVIDER=ollama python -c ...` needs `PYTHONPATH=src` because `src/finroot/schemas/__init__.py` uses `from finroot.*` style imports that require `src/` on the Python path. Pytest handles this automatically via `pythonpath = ["src"]` in `pyproject.toml`. See gotcha G-1.

## Tests
- `tests/unit/test_config.py` — 24 tests, all pass
- Coverage: `TestSettingsDefaults` (4), `TestSettingsEnvOverride` (4), `TestGetSettingsCaching` (3), `TestPromptRegistry` (7), `TestAssertSettings` (5), `TestPrintStartupBanner` (1)

## Decisions / deviations
- Used `lru_cache` for `get_settings()` caching (was `functools.cache` for Python 3.11 compat, but `lru_cache` is fine too).
- PromptRegistry seeds 3 default prompts as placeholders per the task. Uses `(name, version)` tuple key with `version="latest"` fallback to highest-sorted version.
- `assert_settings` does not validate provider membership (redundant — Pydantic enums enforce it at construction time).
- Acceptance command #2 requires `PYTHONPATH=src` prefix (see gotchas).

## Surprises / gotchas
- G-1 added to `docs/waves/wave-1-gotchas.md`: `src/finroot/schemas/__init__.py` uses `from finroot.*` imports requiring `src` on PYTHONPATH.

## Follow-ups (for orchestrator triage — do NOT build now)
- Schemas `__init__.py` import style should be updated to `src.finroot.*` style or relative imports so the project works without `PYTHONPATH=src` in standalone `python -c` usage.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
