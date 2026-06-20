# Repository Structure + Cleanup Plan

> Meta-doc for repo health (T2). Run `/audit --type=docs-sync` to refresh.

## Last audit: 2026-06-19 (baseline)

## Current state
- Top-level files: lean (kernel docs + configs). Target: under ~25 root entries.
- `attic/`: empty (nothing superseded yet).
- `resources/brainstorm/`: 12 LLM design inputs (intentional reference, not shipped code).
- `src/`: interface stubs only (implementation lands per wave).

## Folder ownership recap (full map: HIERARCHY.md)
| Folder | Owner | Reviewed |
|---|---|---|
| `orchestrator/`, `plan/`, `.specify/`, `docs/` | Orchestrator | 2026-06-19 |
| `src/`, `tests/`, `data/`, `config/`, `scripts/` | Workers | 2026-06-19 |
| `work/` | Both (disjoint) | 2026-06-19 |

## Drift indicators (checked by docs_sync.yml / validate.sh)
- Files referenced in CLAUDE.md must exist (FM-03).
- `src/` modules not imported by anything → candidates for `attic/`.
- SHIPPED waves in EXECUTION.md must have commit hashes (FM-01).
- ADRs > 1y untouched → "still current?" check.

## Cleanup targets (revisit after a few waves)
- [ ] As waves ship, ensure each generated number in docs traces to `results/metrics.json` (FM-12).
- [ ] Move any superseded prompts to `prompts/archive/`, superseded docs to `docs/historical/`.

## Next audit due: after wave-2 ships.
