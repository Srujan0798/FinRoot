# Task wave-1/03 — Hash-Chained Audit Backbone

> Self-contained worker brief. Read `work/WORKER_PROMPT.md` + the contract, then build.

## Objective
Implement a tamper-evident, append-only audit trail: each `AuditEvent` hashes
`sha256(prev_hash + canonical(payload) + ts + seq)`, chaining to the previous event. Provide
`append`, `verify_chain`, and `replay` over a JSONL (and/or SQLite) store.

## Why it matters
The audit trail is a core differentiator (PRD O3, Idea 15%) and the backbone of trust (the agent's
every step is reviewable). Tamper-evidence is what makes "auditable" real, not a buzzword.

## Writes (ONLY these)
- `src/finroot/audit/__init__.py`
- `src/finroot/audit/trail.py`
- `src/finroot/audit/store.py`
- `tests/unit/test_audit_chain.py`

## Forbid
Anything else. Use the `AuditEvent` model from `src/finroot/schemas/audit.py` (task 02) — do not
redefine it.

## Contracts to honor
- `schemas.contract.md` → `AuditEvent` shape.
- Interface:
  ```python
  class AuditTrail:
      def __init__(self, path: str | Path): ...
      def append(self, type: str, payload: dict) -> AuditEvent: ...   # computes seq + hash chain
      def verify_chain(self) -> bool: ...                              # False if any event altered
      def replay(self, last_n: int | None = None) -> list[AuditEvent]: ...
  ```

## Steps
1. `store.py`: append-only JSONL writer/reader (canonical JSON, sorted keys, UTC).
2. `trail.py`: `AuditTrail` computing `seq` and `hash` with `prev_hash` chaining; genesis prev_hash = "0"*64.
3. `verify_chain`: recompute each hash; any mismatch → return False (and identify the broken seq).
4. Tests: append 3 events → verify True; mutate one event's payload on disk → verify False (the
   tamper-evidence proof); `replay(last_n)` returns the tail in order.

## Acceptance (paste real output)
```bash
ruff check src/finroot/audit/
pytest tests/unit/test_audit_chain.py -v   # includes the tamper test that MUST flip verify to False
```

## Domain rules
Never silently repair a broken chain — report it (FM-11). Append-only; never rewrite past events.

## Report
`work/reports/wave-1/03-audit-trail-backbone.report.md`.
