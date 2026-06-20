# Governance — Risk Tiering

Every action is classified and gated. Pairs with `blast-radius.md`.

| Tier | Examples | Gate |
|---|---|---|
| **T0 — Auto** | read files, grep, run tests, lint | execute immediately |
| **T1 — Log + proceed** | write to `src/`, modify tests | log to MEMORY.md / events, proceed |
| **T2 — Await approval** | add deps, change CI, modify migrations/schemas, new MCP server | pause, ask Srujan |
| **T3 — Block** | `rm -rf`, force-push, drop tables, exfiltrate data | block unconditionally |

## FinRoot-specific gates
- **Any code that could move money or place a trade** → T3 block. FinRoot is decision-support only.
- **Committing data with possible PII (a real Digital Twin)** → T2; scrub or synthesize first.
- **Adding a closed-API dependency to a core path** → T2; must keep a sovereign/offline fallback.
- **Changing the tax engine constants** → T2; requires a unit test against known cases + ADR.

## Mapping to blast radius
r3+ ⇒ T2 minimum (await approval). r5 ⇒ T3 (block) always. Auto-mode skips r0/r1 only.

## Approval record
T2 approvals are captured as a one-line note in MEMORY.md and (if architectural) an ADR.
