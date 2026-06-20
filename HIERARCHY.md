# HIERARCHY — Repo Map + Ownership

> What every folder is for and who owns it. Orchestrator = Tier 1 (Claude/Kimi).
> Workers = Tier 2 (Srujan's agents). Keep this current when structure changes (FM-03).

| Path | Purpose | Owner |
|---|---|---|
| `CLAUDE.md` / `KIMI.md` / `AGENTS.md` | Kernel, auto-loaded, identical | Orchestrator |
| `HANDOFF.md` | Current state for cold sessions | Orchestrator |
| `HIERARCHY.md` | This map | Orchestrator |
| `README.md` / `HOW_TO_RUN.md` | Entry point + run instructions | Orchestrator |
| `CHANGELOG.md` | Version history (Keep a Changelog) | Orchestrator (on /ship) |
| `CONTRIBUTING.md` | How agents/humans contribute | Orchestrator |
| `BACKLOG.md` | Parked ideas (not scheduled) | Orchestrator |
| `HALL_OF_SHAME.md` | Failure-pattern archive (learning) | Orchestrator + workers |
| `OS_SETUP.md` | The methodology (kept for regeneration) | Reference |
| `.claude/settings.local.json` | Permissions, MCP, auto-mode | Orchestrator |
| `orchestrator/` | **Tier-1 apparatus** (role, core, commands, skills, agents, hooks, recipes, rules, memory, scripts) | Orchestrator only |
| `work/` | **THE BRIDGE** — orchestrator writes task files, workers read; workers write reports | Both (write-disjoint) |
| `workflows/` | Declarative JSON workflows + state | Orchestrator |
| `.specify/` | Spec-driven dev (constitution, steering, per-wave specs) | Orchestrator |
| `plan/` | PRD · ARCHITECTURE · EXECUTION (3 living strategy docs) | Orchestrator |
| `docs/` | Everything explanatory (waves, decisions/ADRs, operational, audits, schemas, flows, architecture, benchmarks) | Orchestrator |
| `prompts/` | Evolving worker prompts (current/archive/hybrid) | Orchestrator |
| `evals/` | **Reasoning-quality proof (the 35% weapon)** — FRB benchmark, graders, trials, transcripts, reports | Orchestrator (design) + workers (impl in wave-6) |
| `src/finroot/` | Agent code: `agents/ tools/ memory/ reasoning/ workflows/ schemas/ llm/ audit/ evaluation/ utils/` | **Workers** |
| `src/interface/` | `ui/` (Streamlit) · `cli/` (Typer) · `api/` (FastAPI optional) | **Workers** |
| `tests/` | `unit/ integration/ e2e/ golden/ fuzz/ performance/ security/` | **Workers** |
| `data/` | `raw/ samples/ synthetic/ annotations/ gold/ ontology/` (tax rules, golden sets) | Workers |
| `corpus/` | Domain corpus (financial docs for RAG / FRB) | Workers |
| `evidence/` | Eval evidence + reasoning transcripts archive | Workers |
| `models/` | Local model cache (FinBERT sentiment) — versioned | Workers |
| `schema/` | JSON Schema / Pydantic exports · `db_struct.sql` | Workers |
| `config/` | Runtime config (`settings.py`, `prompts.py`) | Workers |
| `scripts/` | Project utility scripts (smoke test, seed data) | Workers |
| `deployment/` | IaC / compose overlays / deploy notes | Workers |
| `resources/` | Reference material · `resources/brainstorm/` = the 12 LLM design inputs | Reference |
| `attic/` | Superseded work — **never deleted** | Orchestrator |
| `logs/` `results/` | Runtime logs · generated metrics (`results/metrics.json` = single source) | Runtime |
| `.github/workflows/` | CI: ci · test · security · evals · perf_regression · docs_sync | Orchestrator |

## Ownership rules
- Only the orchestrator writes `orchestrator/`, `plan/`, `.specify/`, `docs/`, status files.
- Only workers write `src/`, `tests/` (the files named in their task brief's `writes` set).
- Shared/foundation files (schemas, config) are owned by ONE early task to avoid collisions (FM-13).
- Nothing is deleted: superseded → `attic/`, `docs/historical/`, `prompts/archive/`.
