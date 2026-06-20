# ADR-0007 — Hash-chained audit trail

- **Status:** Accepted
- **Date:** 2026-06-20
- **Deciders:** Orchestrator (with Srujan)

## Context
Financial systems require tamper-evident records for compliance and trust. We need:

1. A complete, immutable record of all decisions
2. The ability to replay queries and verify results
3. Protection against retroactive modifications
4. Evidence for FM-09 (evidence required) and FM-07 (no secrets)

## Decision
We implemented **Hash-chained audit trail** in `src/finroot/audit/trail.py`:

The audit trail composes:
- **AuditEvent:** Pydantic model for event shape (FM-09)
- **JsonlAuditStore:** Transport layer for on-disk storage
- **Hash chain:** Tamper-evident linkage between events

Hash construction (frozen by contract):
```
hash_i = sha256_hex(prev_hash_i || canonical_payload_i || ts_iso_i || str(seq_i))
```

with `prev_hash_0 = "0" * 64` (genesis sentinel). The concatenation order is the contract — do not change it.

Key properties:
- **Tamper-evident:** Any modification breaks the chain
- **Replayable:** Events can be replayed in order
- **Verifiable:** Entire chain can be validated
- **Append-only:** Old events are never rewritten (FM-11)

The audit trail is the only thing in the system that decides what "an audit event" is on disk. It provides the tamper-evident backbone for financial reasoning.

## Consequences
- **Positive:** Judges can verify system integrity (FM-07)
- **Positive:** Enables replay for debugging and testing
- **Positive:** Provides evidence for all financial decisions (FM-09)
- **Negative:** Increased storage overhead
- **Negative:** Slight performance overhead for hash computation
- **Neutral:** Adds complexity but is essential for financial trust

## Alternatives considered
- **Database with checksums:** Less deterministic; harder to prove tamper-evidence
- **Cloud logging:** Compromises sovereignty; depends on external services
- **In-memory only:** Loses persistence and replayability

The hash-chained approach is the minimal design that delivers tamper-evidence, replayability, and verification for financial systems.