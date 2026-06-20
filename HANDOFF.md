# HANDOFF — Current State

> The single source of truth for "where are we right now." Rewritten to current truth on every
> `/ship` and at the end of every session (FM-01, FM-14). A cold session reads this FIRST.

## Snapshot
- **Project:** FinRoot — Sovereign, Reasoning-First AI Financial Agent
- **Tier:** T2 (Production) · **Archetype:** hackathon/competition + research-ml emphasis
- **Phase:** ALL 8 WAVES SHIPPED — submission ready
- **Latest commit:** `ef1626f` (785 tests, ruff clean, FOUNDATION OK)
- **Orchestrator:** Claude Code / Kimi (interchangeable)
- **Workers:** Srujan's agent swarm (OpenCode CLI windows / external agents)

## What exists now — all 8 waves shipped and verified
- `src/finroot/llm/` — Mock/Ollama/Groq/OpenAI provider abstraction (20 tests)
- `src/finroot/schemas/` — Pydantic v2: enums, finance, recommendation, audit, AgentState (50 tests)
- `src/finroot/audit/` — Hash-chained JSONL audit trail: append/verify_chain/replay (24 tests)
- `src/finroot/utils/config.py` — Startup assertions + banner
- `config/settings.py` — pydantic-settings, `FINROOT_*` env prefix, `get_settings()`
- `config/prompts.py` — Prompt registry
- `src/finroot/tools/` — 12 tools: market, fundamentals, news, sentiment, risk, portfolio_sim, tax, macro, currency, profile, documents, watchlist
- `src/finroot/memory/` — WorkingMemory, SemanticMemory (ChromaDB+JSON fallback), DigitalTwin (SQLite), MemoryManager
- `src/finroot/agents/` — IntentClassifier, 6 specialized ReAct agents + orchestrator
- `src/finroot/workflows/` — LangGraph Plan-and-Execute graph + context assembler + synthesizer
- `src/finroot/reasoning/` — 5-axis SelfCritic, Refinement loop, PrudentialVerifier, SelfConsistency, Explainability
- `src/finroot/evaluation/` — FRB harness, baselines (RAG + SingleAgent), report generator
- `src/interface/` — answer() entry, Typer CLI, Streamlit dark UI (4 tabs: Chat, Trace, Twin, Harness)
- `evals/graders/` — deterministic code-based + LLM-judge graders + human review template
- `data/gold/frb_questions.json` — 32-question FRB bank (7 domains, class-balanced, adversarial traps)
- `data/tax_rules.json` — Indian FY 2024-25 tax rules (deterministic)
- `data/samples/` — 3 DigitalTwin profiles + conversation fixture
- `scripts/smoke_test.py` — End-to-end smoke test → `FOUNDATION OK`
- `scripts/capture_demo.py` — Generates demo transcripts (4 showcase queries)
- `scripts/make_submission.sh` — Packages submission zip
- `scripts/run_evals.py` — FRB benchmark CLI
- `Dockerfile` + `docker-compose.yml` — One-command spin-up, mock default
- `docs/decisions/` — 6 ADRs (MADR format)
- `docs/business/` — 7-min demo script, presentation outline, executive summary
- `docs/architecture/architecture.mmd` — Mermaid architecture diagram
- `results/metrics.json` — THE measured proof (FinRoot 0.686 vs RAG 0.090 = 7.6× lift)
- `.github/workflows/` — CI (6 workflows)
- **785 unit tests passing, ruff clean across all src/**

## FRB Results (measured at `as_of_sha = ef1626f`)
| System | pass@1 | mean score | Lift vs RAG |
|---|---:|---:|---:|
| Baseline RAG | 0.000 | 0.090 | — |
| Single-agent | 0.031 | 0.209 | +2.3× |
| **FinRoot (full)** | **0.344** | **0.686** | **+7.6× (+662%)** |

Per-domain: portfolio 0.73, tax 0.71, general 0.76, risk 0.67, cashflow 0.63, credit 0.63, news_impact 0.54.

## Demo path (works fully offline, no API keys)
```bash
# CLI
PYTHONPATH=src python3 -m interface.cli --mock "Review my portfolio and flag risks"

# Streamlit UI
PYTHONPATH=src streamlit run src/interface/ui/app.py

# Docker
docker compose up -d  # UI at localhost:8501, mock mode

# Full benchmark
PYTHONPATH=src python3 -m scripts.run_evals --mock --k 2
```

## Known gotchas (see docs/waves/wave-*-gotchas.md)
- G-1: Use `PYTHONPATH=src:. ` for standalone commands (pytest auto-handles via pyproject.toml)
- G-2: Parameter named `type` shadows built-in — use `event_type` or `.__class__.__name__`
- G-3: `config/settings.py` must NOT import from `finroot.*` (circular). `llm_provider` is `str`.
- G-4: `answer()` saves/restores `FINROOT_LLM_PROVIDER` env var (don't leak mock flag to tests)
- G-5: Intent routing: emergency-fund/leverage phrases → RISK (prudence engages)

## Open decisions for Srujan (none blocking)
- Live data API keys (AlphaVantage / NewsAPI / Groq) — optional; Mock + Ollama work offline.
- Final demo narrative owner (wave-8) — script written, capture_demo.py generates transcripts.

## Last session note
2026-06-20: All 8 waves shipped. 785 tests, ruff clean, FOUNDATION OK. Submission ready.
Measured FRB lift: FinRoot 0.686 vs RAG 0.090 = 7.6× (+662%). Demo works fully offline.
