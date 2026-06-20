# Task wave-2/03 — Financial Digital Twin + SQLite Persistence

> Read `work/WORKER_PROMPT.md` then build. One self-contained task; stop when report is written.

## Objective
Implement the `DigitalTwin` Pydantic model (the user's financial profile) and `DigitalTwinStore`
(SQLite-backed persistence with JSON fallback). This is the core "personal context" object that
makes FinRoot sovereign and individual-centric.

## Writes (ONLY these)
- `src/finroot/memory/digital_twin.py`
- `schema/db_struct.sql`
- `tests/unit/test_digital_twin.py`

## Forbid
`src/finroot/memory/working.py`, `semantic.py`, `manager.py`, `__init__.py` (other tasks).

## Contract
Read `.specify/specs/wave-2/contracts/memory.contract.md` § DigitalTwin.

## Steps
1. `RiskTolerance`, `InvestmentHorizon` enums (str, Enum — contract values exactly).
2. `DigitalTwin` Pydantic v2 model (`extra="forbid"`, UTC datetimes):
   - All fields per contract.
   - `model_validator` ensures `monthly_expenses <= monthly_income * 2` (sanity check — warns, not hard-fail).
   - `@property monthly_surplus` → `monthly_income - monthly_expenses`.
3. `DigitalTwinStore`:
   - `__init__(db_path)` — creates SQLite DB + table if not exists (schema matches `schema/db_struct.sql`).
   - `save(twin)` — upsert; updates `updated_at` automatically.
   - `load(user_id)` — raises `KeyError` if not found (FM-11).
   - `list_ids()` → `list[str]`.
   - `delete(user_id)` → `None`.
   - JSON fallback: if `sqlite3` unavailable (shouldn't happen, stdlib) fall back to `{db_path}.json`.
4. `schema/db_struct.sql` — `CREATE TABLE IF NOT EXISTS digital_twins (...)` with all columns.
5. Tests (minimum 15): save/load round-trip, load missing raises KeyError, list_ids, delete, monthly_surplus property, enum validation, Pydantic validation errors, SQLite persistence (temp file), updated_at changes on re-save.

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_digital_twin.py -v
ruff check src/finroot/memory/digital_twin.py
```

## Report
`work/reports/wave-2/03-digital-twin.report.md`
