# Blast Radius

Per Anthropic "How we contain Claude across products." Every action has a worst-case radius.

| Radius | Examples | Containment |
|---|---|---|
| **r0 — Read-only** | read files, grep, list | none needed |
| **r1 — Local repo** | write `src/`, run tests | auto allowed; git protects |
| **r2 — Local services** | apply dev DB migration, write Chroma/SQLite | confirm; reversible |
| **r3 — Remote services** | push to GitHub, call a live financial API, send Slack | confirm; possibly reversible |
| **r4 — External humans** | email, file tickets | always confirm; hard to reverse |
| **r5 — Money / data loss** | place a trade, move funds, drop prod data | **block by default** |

## FinRoot rule
FinRoot the *product* is capped at r0–r1 (read market data, reason, write local audit). It must
NEVER reach r5. Trade-execution tools are out of scope and blocked.

## Build-time mapping
- r3+ ⇒ governance tier T2 (await approval) minimum.
- r5 ⇒ governance tier T3 (block) always.
- Auto-mode skips permission prompts for r0/r1 only; r2+ always pauses.

## Implementation
`hooks/pre-tool-use.sh` classifies the call, records the radius in `events.jsonl`, and pauses or
blocks per tier. Live-data tools log every external call with its radius.
