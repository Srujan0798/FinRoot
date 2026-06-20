# Changelog

All notable changes to FinRoot are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · [Semantic Versioning](https://semver.org/).

## [Unreleased]
### Added
- Wave-by-wave implementation tracked in `plan/EXECUTION.md`. Each shipped wave appends here.

## [0.1.0] — 2026-06-19
### Added
- **Project OS-Setup scaffold (T2).** Complete dual-tier agentic structure per `OS_SETUP.md`:
  kernel docs, orchestrator apparatus, `.specify/` specs, `evals/` reasoning harness scaffold,
  CI workflows, Docker, config.
- **Strategy docs:** `plan/PRD.md`, `plan/ARCHITECTURE.md`, `plan/EXECUTION.md`.
- **8-wave plan** with dependency graph and disjoint write-sets; `work/wave-1/` task files written.
- **Constitution + scope guard + failure-mode guardrails** wired into pre-commit + CI + review.
- Brainstorm design inputs (12 LLM proposals) archived under `resources/brainstorm/`.

[Unreleased]: https://example.com/finroot/compare/v0.1.0...HEAD
[0.1.0]: https://example.com/finroot/releases/tag/v0.1.0

## [1.0.0] — 2026-06-20
### Added
- **Full PS-1 submission, all 12 waves shipped.** 1002 unit + integration tests passing
  (9 skipped), ruff clean across all `src/` and `tests/`, FOUNDATION OK.
- **Wave 1 — Foundation:** LangChain + LangGraph scaffold, Pydantic v2 schemas, hash-chained
  JSONL audit trail, Mock/Ollama/Groq/OpenAI provider abstraction, base tool + agent interfaces.
- **Wave 2 — Memory & Digital Twin:** WorkingMemory, SemanticMemory (ChromaDB + JSON fallback),
  DigitalTwin (SQLite, goals/risk/horizon/holdings/tax-bracket), MemoryManager.
- **Wave 3 — Tool Ecosystem:** 12 tools across market/fundamentals/news/sentiment/risk/portfolio_sim/
  tax/macro/currency/profile/documents/watchlist with caching, rate-limit, loud-fail, audit hooks.
- **Wave 4 — Core Agents & Orchestration:** LangGraph Plan-and-Execute orchestrator + 6 specialized
  ReAct sub-agents (Intent · Market · News · Portfolio · Risk · Tax); intent → plan → execute →
  synthesize pipeline wired with tools and memory.
- **Wave 5 — Self-Critic & Reasoning Layer:** 5-axis SelfCritic (correctness/risk-awareness/
  actionability/explainability/evidence), Refinement loop, Rooted Prudence verifier, SelfConsistency,
  Explainability assembly. The 35%-weight reasoning-quality weapon.
- **Wave 6 — Evaluation Harness (FRB):** 83-question FRB bank across 11 financial domains with
  class-balanced, adversarial-trap design. Deterministic code-based + LLM-judge graders. RAG and
  Single-agent baselines for direct comparison. `results/metrics.json` single source of truth.
- **Wave 7 — Interface & Demo:** Streamlit dark-mode UI (4 tabs: Chat, Reasoning Trace, Digital Twin,
  Harness) + Typer CLI + `answer()` programmatic entry. Mock mode by default for zero-friction judging.
- **Wave 8 — Deploy, Docs & Submission:** Dockerfile + docker-compose, 6 MADR-format ADRs, 7-minute
  demo script, 6-slide deck, executive summary, architecture diagram (Mermaid + rasterized PNG),
  `make_submission.sh` packager.
- **Wave 9–11 — Hardening & ultra upgrades:** FRB expansion to 83 tasks (11 domains), Plotly charts,
  FastAPI surface (`/answer`, `/health`), streaming reasoning trace, golden tests, security tests,
  grader tuning, CI/CD workflows.
- **Wave 12 — Docs & demo polish:** SUBMISSION_MESSAGE.md (≤250 words, paste-ready), JUDGE_QUICKSTART.md
  (30-second zero-key judge run), 6-slide speaker-ready deck, demo video shot list, README hero embed
  with trap-refusal screenshot, hero CLI demo cast.

### Measured (this release)
- FRB at HEAD `2e14992`: **FinRoot 0.778 mean** vs **RAG 0.341 mean** = **+128.5% composite lift**
  across 83 graded tasks across 11 financial domains.
- Domain highlights: portfolio 0.83, tax 0.85, general 0.90, news_impact 0.73, risk 0.78.
- The RAG baseline mean of 0.341 cannot satisfy most tasks' must-mention + must-not + citation
  requirements — FinRoot's structured 6-agent pipeline closes that gap measurably.

### Security / privacy
- No secrets committed; `.env.example` placeholders only; `.dockerignore` excludes `.env*`.
- No raw prompts or judge cheat-sheets shipped (`docs/SCOPE_GUARD.md` enforced).
- Hash-chained audit trail keeps every reasoning step tamper-evident.

[1.0.0]: https://github.com/Srujan0798/FinRoot/compare/v0.1.0...v1.0.0
