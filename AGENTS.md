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

## Developer workflow (added in wave-15)

```bash
make session-start    # one-page context summary (HEAD, metric, dirty tree, zip)
make test-fast        # run pytest skipping @pytest.mark.slow
make test-cold        # 3x cold suite verifier (with data/ hermeticity check)
make coverage         # pytest with coverage, fail if below threshold
make validate         # structural + execution + doc-drift checks
make validate-docs    # scan .md files for stale SHA / metric references
make validate-links   # check that internal .md cross-references resolve
make metrics-drift    # compare two metrics.json files; exit 1 if regression
make test-pyramid     # print test counts by category + time budget
make dep-audit        # check for outdated / vulnerable dependencies
make doctor           # smoke-check all integrations
make ship-prep        # regenerate metric + rebuild zip + verify
make ci               # full quality gate (lint + test-fast + coverage + validate + doctor)
```

`make help` prints all available targets with one-line descriptions.

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

Pre-commit runs: `ruff --fix`, `ruff-format`, trailing whitespace, end-of-file, check-yaml/json, detect-private-key, plus three custom hooks:
- `block-secrets` (FM-07) — no secrets in commits (real-key-shape detection; doc text allowed)
- `execution-no-drift` (FM-01) — `plan/EXECUTION.md` matches reality
- `docs-no-drift` — `.md` files cite current HEAD + canonical FinRoot mean (see `orchestrator/scripts/validate_docs.sh`)

Pre-push: optional `orchestrator/hooks/pre-push` hook runs `validate_execution.sh` + `validate_docs.sh` before `git push`. Install with `ln -s ../../orchestrator/hooks/pre-push .git/hooks/pre-push`.

## Test markers

```python
@pytest.mark.wave1        # foundation tests
@pytest.mark.integration  # cross-module
@pytest.mark.e2e          # end-to-end
@pytest.mark.golden       # hand-graded reasoning quality
@pytest.mark.slow         # subprocess tests (>30s); skip with -m "not slow"
@pytest.mark.stress       # stress tests (concurrency, large inputs); skip with -m "not stress"
```

## Key files to read first

1. `HANDOFF.md` — current state, what's in flight
2. `plan/EXECUTION.md` — wave status table
3. `docs/SCOPE_GUARD.md` — IN / OUT / LATER scope rules
4. `HIERARCHY.md` — full directory ownership map
