# Task wave-1/02 — Pydantic Schemas + LangGraph State

> Self-contained worker brief. **Dispatch this FIRST** — the other wave-1 tasks import these types.
> Read `work/WORKER_PROMPT.md` + the contract, then build exactly to it.

## Objective
Implement the core Pydantic v2 schemas and the LangGraph `AgentState` exactly as specified in the
contract: enums, `Citation`, `Recommendation` (the user-facing output contract), `AgentState`, and
`AuditEvent` (shared shape with task 03).

## Why it matters
This is the typed spine of the whole system (Architecture 30%, Code 20%). The `Recommendation`
validator enforcing "numeric content ⇒ citations required" is a structural guard for the 35% reasoning
honesty (FM-11). Freezing this first prevents two tasks redefining a type (FM-13).

## Writes (ONLY these)
- `src/finroot/schemas/__init__.py`
- `src/finroot/schemas/enums.py`
- `src/finroot/schemas/finance.py`
- `src/finroot/schemas/recommendation.py`
- `src/finroot/schemas/state.py`
- `src/finroot/schemas/audit.py`
- `tests/unit/test_schemas.py`

## Forbid
Anything outside `src/finroot/schemas/**` + that test. Do NOT implement audit *logic* (task 03) —
only the `AuditEvent` model lives here.

## Contracts to honor
- `.specify/specs/wave-1/contracts/schemas.contract.md` — implement names, fields, and invariants
  EXACTLY. This file is the contract; deviations require an orchestrator ADR, not a worker choice.

## Steps
1. `enums.py`: `Intent`, `Domain`, `ConfidenceLevel`, `RiskBand`, `Provider` (per contract).
2. `finance.py`: domain value objects (e.g., `Holding`, `Money`, `Horizon`) the twin/tools will use.
3. `recommendation.py`: `Citation`, `Recommendation` with a validator: if `analysis` contains digits
   and `citations` is empty → `ValueError` (FM-11).
4. `state.py`: `AgentState` with `extra="forbid"`, tz-aware UTC datetimes, lossless round-trip.
5. `audit.py`: `AuditEvent` (ts, seq, type, payload, prev_hash, hash) — shape only.
6. Tests: round-trip serialize/deserialize; the citation validator rejects uncited numeric analysis;
   `extra="forbid"` rejects unknown fields.

## Acceptance (paste real output)
```bash
ruff check src/finroot/schemas/
python -c "from finroot.schemas.state import AgentState; s=AgentState(query='hi'); print(AgentState.model_validate_json(s.model_dump_json()).query)"
pytest tests/unit/test_schemas.py -v
```

## Domain rules
`Recommendation` with numbers but no citations is INVALID. Confidence is always set. UTC tz-aware times.

## Report
`work/reports/wave-1/02-pydantic-schemas-state.report.md`.
