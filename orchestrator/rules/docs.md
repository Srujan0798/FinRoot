# Rule — Docs (applies to `docs/**`, root markdown)

- Derived content (numbers, metrics, benchmark results) is GENERATED, never hand-typed (FM-05/12).
  Source of truth: `results/metrics.json` + `evals/reports/`. Stamp "as of <sha>".
- Every committed reference resolves — before renaming/deleting, grep for inbound links and fix (FM-03).
- One source per fact. Status lives in `EXECUTION.md` (one row per wave); don't restate it elsewhere.
- ADRs in `docs/decisions/` for any architectural or scope decision; number them sequentially.
- Wave gotchas captured DURING the wave in `docs/waves/wave-N-gotchas.md`, not after.
- Superseded docs → `docs/historical/`, never deleted.
- Keep the kernel (`CLAUDE.md`) lean; deep detail belongs in `docs/` and lazy-loads.
