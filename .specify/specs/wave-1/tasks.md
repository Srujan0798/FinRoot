# Wave-1 Tasks — index

> The dispatchable task files live in `work/wave-1/`. This is the spec-side index + acceptance map.
> Each task is self-contained; workers also read `work/WORKER_PROMPT.md`.

| # | File | Owns (writes) | Acceptance (worker must show output) |
|---|---|---|---|
| 01 | `work/wave-1/01-llm-provider-layer.md` | `src/finroot/llm/**` | `python -c "from finroot.llm import get_provider; print(get_provider('mock').complete('hi'))"`; provider unit tests pass |
| 02 | `work/wave-1/02-pydantic-schemas-state.md` | `src/finroot/schemas/**` | `AgentState` round-trip test; mypy/pydantic validation passes |
| 03 | `work/wave-1/03-audit-trail-backbone.md` | `src/finroot/audit/**` | tamper test fails verification; append+verify+replay tests pass |
| 04 | `work/wave-1/04-config-settings.md` | `config/**`, `src/finroot/utils/config.py` | settings load from env+defaults; prompt registry test passes |
| 05 | `work/wave-1/05-base-tool-agent-interfaces.md` | `src/finroot/tools/base.py`, `src/finroot/agents/base.py` | base-class contract tests (cache/rate-limit/loud-fail/audit hook) pass |
| 06 | `work/wave-1/06-project-bootstrap-ci.md` | `scripts/smoke_test.py`, `pyproject.toml`, `.github/workflows/ci.yml`, `src/finroot/__init__.py` | `python scripts/smoke_test.py` prints `FOUNDATION OK`; CI green |

## Cross-cutting acceptance (orchestrator, after all merge)
```bash
ruff check src/ && pytest tests/unit -v && python scripts/smoke_test.py
```
All green → ship wave-1.
