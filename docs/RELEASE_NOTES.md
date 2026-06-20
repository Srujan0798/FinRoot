# FinRoot v1.0.0

## What is FinRoot?

FinRoot is a sovereign, reasoning-first AI financial agent built with LangChain, LangGraph, Pydantic v2,
ChromaDB, and SQLite. It delivers institutional-grade financial reasoning to individual investors and small
family offices — locally, explainably, and with a tamper-evident audit trail. Unlike chatbot wrappers that
summarize price feeds, FinRoot plans multi-step tool calls, shows its reasoning, flags risk, cites evidence,
self-critiques, and keeps a full chain-of-thought log. It runs offline with local models (Ollama), or
against OpenAI/Groq, and ships with a dark-mode Streamlit UI, a Typer CLI, and Docker packaging.

## Scoring axes (SCALE ML Club PS-1)

| Axis | Weight | FinRoot approach |
|------|--------|------------------|
| **Reasoning Quality** | 35 % | Multi-agent LangGraph pipeline with self-critique, risk flags, confidence labels, and evidence citations. Full reasoning chain exposed to the user. |
| **Agent Architecture** | 30 % | Orchestrator (Tier-1) + Workers (Tier-2) two-tier dispatch. ChromaDB vector memory + SQLite structured + audit store. State-graph with tool routing. |
| **Code Implementation** | 20 % | Pydantic v2 at every boundary, typed errors, ruff-clean, >80 % test coverage, Docker + docker-compose. |
| **Solution Idea** | 15 % | Sovereign-first: local model default, offline fallback, no blind reliance on closed APIs. Tamper-evident audit trail. |

## FRB (FinRoot Reasoning Benchmark) headline

> **FinRoot achieves 2.38x lift over a RAG baseline on 83 financial reasoning tasks.**
>
> - FinRoot mean score: **0.795** (79.5 %)
> - RAG baseline mean score: **0.334** (33.4 %)
> - Lift: **137.8 %** (2.38x)
>
> _Metrics stamped as of sha `8d4d03f`._

To refresh the numbers after re-running evals:

```bash
make evals
```

## Quickstart

### Docker (recommended)

```bash
git clone https://github.com/<your-org>/finroot.git && cd finroot
cp .env.example .env          # add your API keys (or leave blank for local Ollama)
docker compose up --build
# Streamlit UI → http://localhost:8501
```

### CLI

```bash
pip install -e ".[dev]"
finroot ask "What is my portfolio risk if rates rise 200 bps?"
finroot audit --last 5
```

### Streamlit (local)

```bash
pip install -e ".[dev]"
streamlit run src/interface/ui/app.py
```

## Demo assets

| Asset | Location |
|-------|----------|
| Sample transcripts | `docs/demo/transcript_*.md` |
| Demo capture script | `scripts/capture_demo.py` |
| Screenshots | `docs/demo/` |

## Links

- [Architecture](docs/architecture/architecture.png)
- [Evaluation results](results/metrics.json)
- [Contributing](CONTRIBUTING.md)
- [License: MIT](LICENSE)
