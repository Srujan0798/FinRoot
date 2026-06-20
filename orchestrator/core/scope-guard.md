# Scope Guard (orchestrator copy)

> The canonical IN/OUT/LATER list lives in `docs/SCOPE_GUARD.md`. This is the orchestrator's
> enforcement note. Anti scope-creep (FM-08).

## Enforcement rule
Every task brief must list the files it may touch (`Writes`) and a `Forbid` list. If a worker
proposes work outside the brief, the orchestrator:
1. Rejects it from the current task.
2. If valuable → adds it to `BACKLOG.md` with size + earliest wave.
3. If genuinely required for acceptance → revises the spec via ADR, not silently.

## IN (build these)
The capabilities in PRD §6 (C1–C10) and the 8 waves in EXECUTION.md. Nothing else this round.

## OUT (do not build)
Trade execution / money movement · multi-tenant SaaS / billing / auth portals · mobile apps ·
real-time HFT signals · anything requiring a licensed-advisor disclaimer to be removed.

## LATER (BACKLOG only)
Brokerage sync, FX/multi-currency, voice/WhatsApp, PDF statement ingestion, Postgres+pgvector.
See `BACKLOG.md`.
