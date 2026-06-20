# HANDOFF — Current State

> The single source of truth for "where are we right now." Rewritten to current truth on every
> `/ship` and at the end of every session (FM-01, FM-14). A cold session reads this FIRST.

## Snapshot
- **Project:** FinRoot — Sovereign, Reasoning-First AI Financial Agent
- **Tier:** T2 (Production) · **Archetype:** hackathon/competition + research-ml emphasis
- **Phase:** ALL 12 WAVES SHIPPED — submission ready for SCALE ML Club PS-1
- **Latest commit:** `8d4d03f` (1066 tests passing / 9 skipped, ruff clean, FOUNDATION OK)
- **Orchestrator:** Claude Code / Kimi / Codex (interchangeable)
- **Workers:** Srujan's agent swarm (OpenCode CLI windows / external agents)

## What exists now — all 12 waves shipped and verified
- `src/finroot/llm/` — Mock/Ollama/Groq/OpenAI provider abstraction (20 tests)
- `src/finroot/schemas/` — Pydantic v2: enums, finance, recommendation, audit, AgentState (50 tests)
- `src/finroot/audit/` — Hash-chained JSONL audit trail: append/verify_chain/replay (24 tests)
- `src/finroot/utils/config.py` — Startup assertions + banner
- `config/settings.py` — pydantic-settings, `FINROOT_*` env prefix, `get_settings()`
- `config/prompts.py` — Prompt registry
- `src/finroot/tools/` — 14 tools: market, fundamentals, news, sentiment, risk, portfolio_sim, tax, macro, currency, profile, documents, watchlist, goal_planner, pdf_ingestion
- `src/finroot/memory/` — WorkingMemory, SemanticMemory (ChromaDB+JSON fallback), DigitalTwin (SQLite), MemoryManager
- `src/finroot/agents/` — IntentClassifier, 6 specialized ReAct agents + orchestrator
- `src/finroot/workflows/` — LangGraph Plan-and-Execute graph + context assembler + synthesizer
- `src/finroot/reasoning/` — 5-axis SelfCritic, Refinement loop, PrudentialVerifier, SelfConsistency, Explainability, CounterfactualGenerator, FxAwareAnalyzer
- `src/finroot/audit/` — Hash-chained JSONL audit trail + OpenTelemetry-style distributed tracing
- `src/finroot/evaluation/` — FRB harness, baselines (RAG + SingleAgent), report generator
- `src/interface/` — answer() + stream_answer() entry, Typer CLI, Streamlit dark UI (4 tabs: Chat, Trace, Twin, Harness)
- `evals/graders/` — deterministic code-based + LLM-judge graders + human review template
- `data/gold/frb_questions.json` — 83-question FRB bank (11 domains, class-balanced, adversarial traps)
- `data/gold/adversarial_questions.json` — 20-question adversarial eval set (unsafe advice, hallucination, manipulation, bias)
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
- `results/metrics.json` — THE measured proof (FinRoot 0.795 vs RAG 0.334 = +137.8% composite lift)
- `src/interface/api/` — FastAPI surface (`/answer`, `/health`) for headless eval/integration
- `scripts/capture_screenshots.py` — Playwright PNG capture of 4 Streamlit tabs + harness
- `docs/demo/screenshots/` — 5 PNGs (chat, trace, trap refusal, twin, harness)
- `docs/architecture/architecture.png` — Rasterized architecture diagram
- `docs/business/slides.md` — 6-slide speaker-ready deck
- `docs/business/demo_video_shotlist.md` — Scene-by-scene recording guide
- `docs/SUBMISSION_MESSAGE.md` — ≤250-word paste-ready message for organizers
- `docs/JUDGE_QUICKSTART.md` — 30-second zero-key judge run
- `.github/workflows/` — CI (6 workflows)
- **1066 unit + integration tests passing** (9 skipped), ruff clean across all src/

## New features (added post wave-12)
- **Streaming UI** — `stream_answer()` yields real-time progress updates; Chat component shows status as pipeline executes
- **Counterfactual Explanations** — `CounterfactualGenerator` produces "what would change this recommendation" from assumptions/risks/confidence
- **Goal Planner Tool** — `GoalPlannerTool` calculates SIP, corpus, and allocation for financial goals with inflation adjustment
- **FX-Aware Reasoning** — `FxAwareAnalyzer` assesses multi-currency portfolios for FX risk, hedging needs, NRI-specific advice
- **PDF Statement Ingestion** — `PDFIngestionTool` parses CDSL/NSDL CAS, AMC statements to auto-build Digital Twin
- **Distributed Tracing** — OpenTelemetry-style spans with JSONL export for pipeline observability
- **FinBERT Agreement Study** — `evals/graders/agreement_study.py` calculates Cohen's kappa for grader calibration
- **Adversarial Eval Set** — 20 red-team prompts testing refusal of unsafe advice, hallucination, manipulation, bias

## FRB Results (measured at `as_of_sha = 8d4d03f`)
| System | pass@1 | mean score | Lift vs RAG (mean) |
|---|---:|---:|---:|
| Baseline RAG | 0.289 | 0.334 | — |
| Single-agent | 0.181 | 0.329 | −1.5% |
| **FinRoot (full)** | **0.193** | **0.795** | **+137.8% (composite)** |

Per-domain (FinRoot mean score): general 0.92, tax 0.87, portfolio 0.85, credit 0.85,
news_impact 0.77, risk 0.77, international 0.75, behavioral 0.74, cashflow 0.74,
estate_planning 0.69, insurance 0.66. The headline metric is the **mean reasoning-quality
score** (0–1), which weighs must-mention + must-not + citation completeness across 83 graded
tasks.

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
2026-06-21: All 12 waves shipped + 8 new features added. 1066 tests passing (9 skipped), ruff clean, FOUNDATION OK.
New features: streaming UI, counterfactual explanations, goal planner, FX-aware reasoning, PDF ingestion, distributed tracing, adversarial eval set, FinBERT agreement study.
Fixed pre-existing bugs: `Confidence` → `ConfidenceLevel` import in graph.py, fundamentals mock returning hash-based values.
Measured FRB lift at HEAD `8d4d03f`: FinRoot 0.795 vs RAG 0.334 = +137.8% composite lift.
83 graded tasks across 11 financial domains. Demo works fully offline (Mock mode).
Submission zip: `finroot-submission.zip` (1.05 MB, 327 files, no secrets).
