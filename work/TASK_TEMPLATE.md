# Task <WAVE>/<NN> — <Title>

> Self-contained worker brief. A stateless agent must be able to execute this with no other context
> except `work/WORKER_PROMPT.md` and the referenced contracts. Read those, then build.

## Objective
<One paragraph: exactly what to build.>

## Why it matters
<Link to scoring weight + PRD capability. Keeps the worker aligned.>

## Writes (you may create/modify ONLY these)
- `path/one`
- `path/two`

## Forbid (do NOT touch)
- Everything else, especially other tasks' `writes` sets and `orchestrator/`, `plan/`, `docs/`.

## Contracts to honor
- `.specify/specs/<wave>/contracts/<name>.contract.md` — implement exactly (names, types, invariants).

## Steps
1. <ordered, concrete step>
2. ...

## Acceptance (paste the REAL command output into your report — FM-09)
```bash
<command 1>     # expected: <what proves it works>
<command 2>
```

## Domain rules (non-negotiable)
- Numbers come from tools and carry a Citation. Never fabricate financial data (FM-11).
- Fail loud — no `except: pass`; missing required input is an error, not a silent default.
- Outputs that recommend action carry rationale + risks + confidence; "do not act yet" is valid.
- Type everything (Pydantic v2). ruff-clean. Tests included.

## Report
Write `work/reports/<wave>/<NN>-<slug>.report.md` using `work/REPORT_TEMPLATE.md`.
Include the acceptance command output. If you hit a surprise, also add it to
`docs/waves/<wave>-gotchas.md`.
