# FinRoot — Agent Instructions

> Sovereign, reasoning-first AI financial agent (LangChain + LangGraph). Python 3.11, Pydantic v2.

## Quick commands

```bash
make install          # pip install -r requirements.txt && pip install -e .
make smoke            # end-to-end foundation check → "FOUNDATION OK"
make lint             # ruff check src/ tests/ scripts/
make test             # pytest (1002 tests, 9 skipped)
make cli ARGS="--mock 'your question'"   # CLI in mock mode
make evals            # FRB benchmark → results/metrics.json
make docker           # full stack (mock default)
```

All commands work offline with zero API keys (mock provider is the default).

## PYTHONPATH gotcha

For standalone `python` commands outside pytest/make, always prefix:
```bash
PYTHONPATH=src python3 -m interface.cli --mock "question"
```
pytest auto-handles this via `pyproject.toml` (`pythonpath = ["src"]`).

## Project structure

| Path | What it is |
|---|---|
| `src/finroot/` | Core agent code: `agents/ tools/ memory/ reasoning/ workflows/ schemas/ llm/ audit/ evaluation/` |
| `src/interface/` | UI (`ui/app.py` Streamlit) + CLI (`cli/` Typer) + API (`api/` FastAPI) |
| `config/` | `settings.py` (pydantic-settings, `FINROOT_*` env prefix) + `prompts.py` |
| `tests/` | `unit/ integration/ e2e/ golden/ fuzz/ performance/ security/` |
| `evals/` | FRB benchmark (83 tasks, 11 domains), graders, trials |
| `orchestrator/` | Tier-1 planning apparatus — do NOT write here |
| `work/` | Task files + reports bridge — read task files, write reports |
| `docs/` | Architecture, ADRs, demo scripts, submission materials |
| `data/` | `gold/frb_questions.json` (83-question bank), `tax_rules.json`, samples |
| `scripts/` | `smoke_test.py`, `run_evals.py`, `capture_demo.py`, `make_submission.sh` |
| `results/metrics.json` | Single source of truth for measured metrics |

## Two-tier methodology

- **Tier 1 (Orchestrator):** Plans, reviews, merges. Never writes `src/` code.
- **Tier 2 (You — Worker):** Implement into `src/`, write tests into `tests/`, report to `work/reports/`.
- Only touch files listed in your task brief's `writes` set. Never edit `orchestrator/`, `plan/`, `.specify/`.

## Critical gotchas

- **G-1:** `config/settings.py` must NOT import from `finroot.*` — circular import. `llm_provider` is `str`, not enum.
- **G-2:** Parameter named `type` shadows built-in — use `event_type` or `.__class__.__name__`.
- **G-3:** `answer()` saves/restores `FINROOT_LLM_PROVIDER` env var — don't leak mock flag to tests.
- **G-4:** Superseded files go to `attic/` — never delete history.
- **G-5:** Metrics live in `results/metrics.json` — regenerate, never hand-type. Stamp with commit SHA.

## Environment

All optional — mock mode needs nothing:
```bash
FINROOT_LLM_PROVIDER=mock|ollama|groq|openai   # default: mock
FINROOT_OLLAMA_BASE_URL=http://localhost:11434
FINROOT_OLLAMA_MODEL=llama3.1:8b
FINROOT_GROQ_API_KEY=    # leave blank to stay sovereign
FINROOT_OPENAI_API_KEY=
```

## Quality gates

Pre-commit runs: `ruff --fix`, `ruff-format`, trailing whitespace, end-of-file, check-yaml/json, detect-private-key, plus two custom hooks:
- `block-secrets` (FM-07) — no secrets in commits
- `execution-no-drift` (FM-01) — `EXECUTION.md` matches reality

## Test markers

```python
@pytest.mark.wave1        # foundation tests
@pytest.mark.integration  # cross-module
@pytest.mark.e2e          # end-to-end
@pytest.mark.golden       # hand-graded reasoning quality
```

## Key files to read first

1. `HANDOFF.md` — current state, what's in flight
2. `plan/EXECUTION.md` — wave status table
3. `docs/SCOPE_GUARD.md` — IN / OUT / LATER scope rules
4. `HIERARCHY.md` — full directory ownership map
