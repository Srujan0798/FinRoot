# Conventions

> Cross-cutting conventions for FinRoot. Path-scoped detail in `orchestrator/rules/`.

## Naming
- Packages/modules: `snake_case`. Classes: `PascalCase`. Constants: `UPPER_SNAKE`.
- Tools end in `Tool` (`MarketDataTool`); sub-agents end in `Agent` (`RiskAssessorAgent`).
- Files mirror their primary class: `market.py` → `MarketDataTool`.

## Layout
- `src/finroot/` is the importable package (src layout). `src/interface/` is UI/CLI/API.
- One responsibility per module. Reasoning logic lives in `reasoning/`, never in tools or UI.

## Data & types
- Pydantic v2 at every boundary; `extra="forbid"` on schemas.
- UTC, timezone-aware datetimes everywhere.
- Money as a typed value object, never raw floats in domain logic.

## Errors & logging
- No bare `except:`; catch specific, log structured, raise/return typed errors (FM-11).
- Structured JSON logs via the project logger; `print` only for CLI user output.

## Financial outputs
- Every numeric claim carries a `Citation` to a tool output.
- Every recommendation: rationale + alternatives + risks + confidence; "do not act yet" is valid.

## Git
- Conventional Commits (`feat:`/`fix:`/`docs:`/`test:`/`chore:`), scoped to the wave/task.
- One logical change per commit. Never commit secrets (FM-07) or generated caches.

## Docs
- Derived numbers are generated from `results/metrics.json`, never hand-typed (FM-05/12).
- Every reference resolves; superseded docs go to `docs/historical/`, never deleted.
