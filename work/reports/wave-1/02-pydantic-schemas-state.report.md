# Report wave-1/02 — Pydantic Schemas & LangGraph State

## Result
DONE

## What I built
- `src/finroot/schemas/enums.py` — `Intent`, `ConfidenceLevel`, `RiskBand`, `Provider`, `Domain`, `Horizon` enums
- `src/finroot/schemas/audit.py` — `AuditEvent` (hash-chained, extra="forbid")
- `src/finroot/schemas/finance.py` — `Money`, `Holding` (quantity optional), `Portfolio`
- `src/finroot/schemas/recommendation.py` — `Citation`, `Recommendation` with citation-required validator (FM-11)
- `src/finroot/schemas/state.py` — `AgentState` (LangGraph-compatible TypedDict-style)
- `src/finroot/schemas/__init__.py` — re-exports all public symbols
- `tests/unit/test_schemas.py` — 50 tests covering all schemas

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_schemas.py
..................................................
50 passed in 0.22s

$ PYTHONPATH=src python3 -m ruff check src/finroot/schemas/ tests/unit/test_schemas.py
All checks passed!
```

## Tests
- 50 tests added · 50 passed · 0 failed

## Decisions / deviations
- `Holding.quantity` made optional (`float | None`, default `None`) so snapshot-only holdings with unknown quantity validate; `market_value` and `unrealized_pnl` return `None` when quantity is absent
- Test syntax error on line 485 (walrus operator misuse) patched by orchestrator: `s.model_validate_json := s.model_dump_json()` → `s.model_dump_json()`
- Ruff import-sort auto-fixed in `test_schemas.py`

## Surprises / gotchas
- Test had a Python syntax error (walrus operator used incorrectly as assignment target inside method call) — fixed and added to gotchas: N (minor, already visible in diff)

## Follow-ups (for orchestrator triage — do NOT build now)
- `AgentState` will need LangGraph `Annotated` reducer support once wave-4 wires orchestrator edges
- Consider adding `Portfolio.total_value` aggregate property in wave-2

## Self-check
- [x] Only touched Writes set (schemas/**, tests/unit/test_schemas.py)
- [x] No fabricated numbers; enums/schemas only (FM-11 n/a here)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, 50/50 tests green (output above)
- [x] No secrets committed (FM-07)
