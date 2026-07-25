# SCALE ML Club PS-1 — Submission Message

> Ready-to-paste message for organizers. ≤ 250 words.

---

**FinRoot — Sovereign, Reasoning-First AI Financial Agent.**

FinRoot gives individual investors institutional-grade, explainable, auditable financial reasoning — locally, on their own terms. Not a chatbot wrapper: a 6-agent LangGraph reasoning pipeline that shows its work, flags risk, cites evidence, self-critiques, and keeps a tamper-evident, hash-chained audit trail.

**Repo:** https://github.com/Srujan0798/FinRoot

**One-line idea:** reasoning-first, audit-evident financial agent that refuses unsafe advice and proves every claim — runs fully offline, no API keys.

**Architecture:** LangGraph Plan-and-Execute, 6 agents, 12 deterministic tools, 4-tier memory + Digital Twin, 5-axis Self-Critic, Rooted Prudence verifier, hash-chained audit. Pydantic v2, ruff-clean, pytest 1000+, Dockerized.

**Run it in 30 seconds (offline, zero keys):**
```bash
git clone https://github.com/Srujan0798/FinRoot.git && cd FinRoot
docker compose up --build
# open http://localhost:8501
```
CLI: `pip install -e .[ui] && PYTHONPATH=src python -m interface.cli --mock "Should I rebalance my 70/30 portfolio before FY-end?"`

**The one headline metric (FRB, 83 tasks, 11 domains):** **FinRoot 0.8741 vs RAG 0.3384 = +158.30% composite lift at HEAD 7d695fc** — `results/metrics.json`.

**Scorecard:** 35% Reasoning — 5-axis Self-Critic + Rooted Prudence + FRB +158% lift. 30% Architecture — LangGraph, 6 agents, 12 tools, Digital Twin, audit chain. 20% Code — modular `src/finroot/`, Pydantic v2, pytest 1000+, ruff-clean. 15% Idea — sovereign, auditable reasoning over your financial twin.

**Links:** demo video `docs/demo/finroot_demo.mp4` · screenshots `docs/demo/screenshots/` · architecture `docs/architecture/architecture.png`.
