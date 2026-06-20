# Wave-1 Plan — Foundation

> The technical plan that turns the spec into 6 parallel-safe tasks with disjoint write-sets.

## Task breakdown (6 tasks, parallel after the shared schema task)
| Task | Title | Writes (owns) | Depends on |
|---|---|---|---|
| 01 | LLM provider layer | `src/finroot/llm/**` | 02 (schemas) |
| 02 | Pydantic schemas + LangGraph state | `src/finroot/schemas/**` | — (first) |
| 03 | Audit-trail backbone (hash-chained) | `src/finroot/audit/**` | 02 |
| 04 | Config + settings + prompt registry | `config/**`, `src/finroot/utils/config.py` | 02 |
| 05 | Base Tool + Agent interfaces | `src/finroot/tools/base.py`, `src/finroot/agents/base.py` | 02, 03 |
| 06 | Project bootstrap + smoke + CI | `scripts/smoke_test.py`, `pyproject.toml`, `.github/workflows/ci.yml`, root `__init__` exports | 01–05 |

**Sequencing:** Task 02 (schemas) ships first or its contract is frozen up front so 01/03/04/05 can
proceed in parallel against the agreed types. Task 06 integrates and proves CI green last.

## Shared contract (freeze before dispatch — FM-13)
All tasks import from `src/finroot/schemas/`. The schema contract is in
`contracts/schemas.contract.md` and must be agreed before 01/03/04/05 start, so no two tasks
redefine a type. Schemas package is owned solely by task 02.

## Parallelism strategy
1. Dispatch task 02 first (or freeze its contract), let it land the schema package.
2. Dispatch 01, 03, 04, 05 in parallel — each writes a disjoint subtree.
3. Dispatch 06 last to wire exports + smoke + CI and prove the acceptance commands.

## Definition of done (wave)
All `spec.md` acceptance commands pass with captured output; `tests/unit` green; CI green;
`EXECUTION.md` row → SHIPPED + commit hash; `HANDOFF.md` rewritten; CHANGELOG bumped.
