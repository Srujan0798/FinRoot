# Wave 1 — Foundation

**Goal:** the typed, sovereign, auditable substrate every later wave imports. Runs in Mock mode
with zero keys. **Status: READY TO DISPATCH.** Spec: `.specify/specs/wave-1/`.

**Why first:** waves 2–8 import these modules; foundation collisions are the costliest (FM-13).

## Tasks (6 — dispatch 02 first/freeze its contract, then 01·03·04·05 in parallel, 06 last)
| # | Task | Suggested agent role | Writes (owns) | Depends |
|---|---|---|---|---|
| 01 | LLM provider layer (Mock/Ollama/Groq/OpenAI) | backend/infra | `src/finroot/llm/**` | 02 |
| 02 | Pydantic schemas + LangGraph state | types/architecture | `src/finroot/schemas/**` | — |
| 03 | Hash-chained audit backbone | security/backend | `src/finroot/audit/**` | 02 |
| 04 | Config + settings + prompt registry | backend | `config/**`, `src/finroot/utils/config.py` | 02 |
| 05 | Base Tool + Agent interfaces | architecture | `src/finroot/tools/base.py`, `src/finroot/agents/base.py` | 02,03 |
| 06 | Bootstrap + smoke test + CI | devops | `scripts/smoke_test.py`, `pyproject.toml`, `.github/workflows/ci.yml`, `src/finroot/__init__.py` | 01-05 |

Task files: `work/wave-1/01..06-*.md`. Each is self-contained.

## Acceptance (wave)
```bash
pip install -r requirements.txt
ruff check src/
python scripts/smoke_test.py            # prints FOUNDATION OK
pytest tests/unit -v
```
## Scoring relevance
Code Implementation (20%) — clean modular typed foundation; Architecture (30%) — provider/tool/agent
abstractions; sets up Reasoning (35%) via the audit + state spine.
