<div align="center">

# FinRoot
### Sovereign · Reasoning-First · Auditable AI Financial Agent

<img src="docs/assets/finroot-logo.svg" width="120" alt="FinRoot logo">

**Institutional-grade financial reasoning for the individual — local, explainable, trustworthy.**

[![Python 3.11](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-passing-2ea44f?logo=pytest&logoColor=white)](#-verification)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![SCALE ML Club — PS-1](https://img.shields.io/badge/SCALE_ML_Club-PS--1-9b59b6)](#)
[![Sovereign: local-first](https://img.shields.io/badge/sovereign-local--first-orange)](#-sovereignty--audit)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

*Built with **LangChain + LangGraph · Pydantic v2 · ChromaDB · SQLite · Streamlit**. Submitted to
SCALE ML Club — Problem Statement 1: **Build an AI Agent for Finance**.*

</div>

<div align="center">

## See it in action

[![FinRoot — Portfolio Analysis + Trap Refusal](docs/demo/screenshots/03_trap_refusal.png)](docs/demo/hero.md)

*Click the image for the full CLI demo — portfolio review, tax calculation, and prudence refusal.*

</div>

---

## The one-line pitch

> **Give an individual investor / small family office institutional-grade, explainable,
> auditable financial reasoning — locally and on their own terms.**

---

## 📉 The problem

Most financial "AI" is a chatbot calling a price API and asking an LLM to summarize. Not advice — a guess with no trace. FinRoot is engineered against every failure:

| Pain | FinRoot's answer |
|---|---|
| **No reasoning shown** | Step-by-step plan + 5-axis self-critic, visible in trace |
| **No risk flags** | Rooted Prudence verifier + risk agent + downside scenarios |
| **No citations** | Every claim grounded to tool output, hash-chained in audit |
| **No memory of you** | Digital Twin: goals, risk, horizon, holdings, tax bracket |
| **No audit trail** | Hash-chained JSONL ledger — every step tamper-evident + replayable |
| **Vendor lock-in** | Sovereign-first: Ollama local, Mock offline, no blind API dependence |

---

## ✅ What FinRoot does

A **multi-agent reasoning pipeline** that decides, defends, and documents.

- **6-agent LangGraph orchestration** — Intent · Market · News · Portfolio · Risk · Tax agents coordinated by Plan-and-Execute supervisor with refine loops
- **14 tools** — market data, fundamentals, news/sentiment, risk + portfolio_sim, tax engine, macro/currency, profile/documents/watchlist, goal planner, PDF ingestion — all with caching, rate-limiting, audit hooks
- **4-tier memory + Digital Twin** — working context · semantic (ChromaDB/JSON) · Digital Twin (SQLite: goals/risk/holdings/tax) · audit trail
- **5-axis Self-Critic** — correctness · risk-awareness · actionability · explainability · evidence. Low scores trigger refinement
- **Rooted Prudence verifier** — guards timeless wealth principles (long-term, downside-first, no overclaiming)
- **Hash-chained audit trail** — every reasoning step, tool call, data source tamper-evident and replayable
- **Sovereign-first** — local Ollama default; offline Mock for zero-friction judging; no closed API dependence
- **FRB Reasoning-Quality harness** — reproducible benchmark proving lift over RAG baseline (`evals/`, `results/metrics.json`)

---

## 🏗 Architecture

![FinRoot Architecture](docs/architecture/architecture.png)

Diagram source: [docs/architecture/architecture.mmd](docs/architecture/architecture.mmd) — re-render with `bash scripts/render_diagram.sh`.

---

## 🎯 Judging-criteria mapping (SCALE ML Club PS-1)

| Weight | Criterion | Where FinRoot earns it |
|---:|---|---|
| **35%** | **Reasoning Quality** | 5-axis Self-Critic + Rooted Prudence + Digital-Twin synthesis + FRB harness vs RAG baseline |
| **30%** | **Agent Architecture** | LangGraph Plan-and-Execute + 6 agents + 14 tools + 4-tier memory + refine loops + audit + LLM abstraction |
| **20%** | **Code Implementation** | Modular `src/finroot/` · Pydantic v2 · 1066 tests · ruff-clean · CI · Docker |
| **15%** | **Solution Idea** | Sovereign, auditable reasoning over your Digital Twin — downside-aware, locally runnable, with proof harness |

---

## 🚀 Quickstart

### Docker (recommended, judge-safe)
```bash
docker compose up --build    # open http://localhost:8501 — Mock mode, zero keys
```

### Local Python
```bash
pip install -e .[ui]
python -m interface.cli --mock "Should I rebalance my 70/30 portfolio before FY-end?"
streamlit run src/interface/ui/app.py
```

### Sovereign (Ollama, fully local)
```bash
ollama pull llama3.1:8b && export FINROOT_LLM_PROVIDER=ollama
streamlit run src/interface/ui/app.py
```

### Verify reasoning quality
```bash
make evals    # FRB harness → results/metrics.json
```

---

## 🖼 Screenshots

All captured in Mock mode via `scripts/capture_screenshots.py`.

| # | Screenshot | What it shows |
|---|---|---|
| 1 | ![Chat](docs/demo/screenshots/01_chat_portfolio.png) | Portfolio-risk query with structured finance card: summary, confidence, risks, actions, citations |
| 2 | ![Trace](docs/demo/screenshots/02_reasoning_trace.png) | Step-by-step plan, tool calls, 5-axis self-critic scores, prudential verifier, citations |
| 3 | ![Trap](docs/demo/screenshots/03_trap_refusal.png) | Refuses unsafe advice ("emergency fund into hot small-cap"), flags risk, offers alternatives |
| 4 | ![Twin](docs/demo/screenshots/04_digital_twin.png) | Digital Twin: profile, risk tolerance, horizon, tax bracket, goals, holdings, allocation chart |
| 5 | ![Harness](docs/demo/screenshots/05_harness.png) | FRB benchmark: composite lift vs RAG, system comparison, per-domain bar chart |

---

## 📊 FRB Results — Reasoning Quality (the 35% proof)

> **Single source of truth: `results/metrics.json`.** Numbers in this table are **regenerated
> from the eval harness**, never hand-typed (FM-12). If the file is absent, regenerate with
> `make evals` (see status note below).

| System | pass@1 | pass@k | pass^k | Mean score (0–1) | Lift vs RAG |
|---|---:|---:|---:|---:|---:|
| Baseline RAG (retrieve + single LLM) | 0.289 | 0.434 | 0.036 | 0.334 | — |
| Single-agent (no critic) | 0.181 | 0.398 | 0.000 | 0.329 | −1.5% |
| **FinRoot (full pipeline)** | **0.193** | **0.193** | **0.193** | **0.795** | **+137.8%** |

**Measured at:** `as_of_sha = 8d4d03f` · `n_tasks = 83` · `k = 3` · `mock = True` · regenerate with `make evals`.

### Per-domain mean scores (FinRoot)

| Domain | Score | | Domain | Score |
|---|---:|---|---|---:|
| general | 0.921 | | risk | 0.765 |
| tax | 0.873 | | international | 0.750 |
| portfolio | 0.852 | | behavioral | 0.740 |
| credit | 0.853 | | cashflow | 0.736 |
| news_impact | 0.767 | | estate_planning | 0.692 |
| | | | insurance | 0.664 |

**Composite lift vs RAG: +137.8%.** RAG baseline 0.334 mean cannot satisfy must-mention + must-not + citation requirements. **FinRoot 0.795 mean across 83 tasks, 11 domains.** Demo transcripts: `docs/demo/transcript_*.md`.

---

## 🛡 Sovereignty + audit trail

**Sovereignty.** Default: **Mock** (offline, deterministic — safe for CI/judging). Production default: **Ollama** (local, your machine, your data). Cloud (Groq, OpenAI) opt-in via env vars. No telemetry, no closed-source prompt dependence, entire stack runs offline.

**Audit trail.** Every step — plan, tool call, retrieved doc, model output, critic verdict, principle check — emitted as structured `AuditEvent` in a **hash-chained ledger** (`src/finroot/audit/`). Each event references previous hash → tampering detectable. Ledger is replayable: feed back into agent → reproduce run bit-for-bit. The answer comes with its proof.

---

## 🗂 Repo map

```
finroot/
├── src/finroot/           ← agent code (agents, tools, memory, reasoning, audit, llm)
├── src/interface/         ← Streamlit UI · Typer CLI · FastAPI
├── config/                ← settings (pydantic-settings) + prompt registry
├── evals/                 ← FRB reasoning-quality benchmark + graders
├── data/                  ← FRB question bank (83 questions), tax rules, sample profiles
├── tests/                 ← unit / integration / golden / fuzz / perf / security
├── results/metrics.json   ← measured metrics (regenerated via `make evals`)
├── scripts/               ← smoke, run_evals, capture_demo, make_submission
├── docs/                  ← architecture, ADRs, demo, business, submission
├── AGENTS.md · HANDOFF.md ← agent instructions + session state
└── Dockerfile · docker-compose.yml ← one-command spin-up
```

---

## 📄 License

[MIT](LICENSE) — see also [CONTRIBUTING.md](CONTRIBUTING.md).