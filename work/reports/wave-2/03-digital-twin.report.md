# Report wave-2/03 — Financial Digital Twin + SQLite Persistence

## Result
DONE

## What I built
- `src/finroot/memory/digital_twin.py` — `RiskTolerance` / `InvestmentHorizon` enums, `DigitalTwin` Pydantic v2 model, `DigitalTwinStore` SQLite-backed persistence with JSON fallback
- `schema/db_struct.sql` — `CREATE TABLE IF NOT EXISTS digital_twins (...)` with all columns
- `tests/unit/test_digital_twin.py` — 33 tests covering model validation, store CRUD, persistence, edge cases

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_digital_twin.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
collected 33 items

tests/unit/test_digital_twin.py .................................        [100%]

============================== 33 passed in 0.87s ==============================

$ ruff check src/finroot/memory/digital_twin.py
All checks passed!

$ ruff check tests/unit/test_digital_twin.py
All checks passed!
```

## Tests
- 33 tests added (TestRiskTolerance: 2, TestInvestmentHorizon: 2, TestDigitalTwin: 15, TestDigitalTwinStore: 14) · 33/33 pass · no coverage data collected

## Decisions / deviations
- `_make_twin` test helper uses `dict.update(**kwargs)` pattern from existing `test_schemas.py` conventions, avoiding keyword conflicts with positional params.
- JSON fallback stores all twins in a single `{db_path}.json` dict (per task spec: `{db_path}.json`), not per-user files as the contract example suggests.
- SQLite `row_factory = sqlite3.Row` used in `_load_sqlite` so column names are accessible as dict keys (avoids integer-index tuple issues).
- `model_validator` for expenses sanity logs a warning rather than raising (per task spec: "warns, not hard-fail").

## Surprises / gotchas
- None encountered; no gotchas file created.

## Follow-ups (for orchestrator triage — do NOT build now)
- None.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
