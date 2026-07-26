# SCALE ML Club PS-1 — Submission Message

> Ready-to-paste message for organizers. ≤ 250 words.

---

**FinRoot — Sovereign, Reasoning-First AI Financial Agent.**

FinRoot gives individual investors institutional-grade, explainable, auditable financial reasoning — locally, on their own terms. Not a chatbot wrapper: a multi-agent LangGraph pipeline that shows its work, flags risk, cites evidence, self-critiques, refuses unsafe advice, and keeps a hash-chained audit trail.

**Repo:** https://github.com/Srujan0798/FinRoot

**One-line idea:** reasoning-first, audit-evident financial agent that refuses unsafe advice and proves every claim — fully offline, no API keys.

**Architecture:** LangGraph Plan-and-Execute, 6 agents, 14 tools, Digital Twin memory, 5-axis Self-Critic, Rooted Prudence, hash-chained audit. Pydantic v2, golden path locks, Dockerized.

**Run (offline, zero keys):**
```bash
git clone https://github.com/Srujan0798/FinRoot.git && cd FinRoot
docker compose up --build
# http://localhost:8501
```
CLI: `pip install -e ".[ui]" && PYTHONPATH=src python -m interface.cli --mock "Should I rebalance my 70/30 portfolio before FY-end?"`

**Headline metric (FRB, 83 tasks, mock k=1, regenerated):** FinRoot mean **0.9114** · pass@1 **1.0000** vs RAG mean **0.3390** = **+168.85%** composite lift at HEAD **b62088f** — `results/metrics.json`.

**Scorecard:** 35% Reasoning — Self-Critic + Prudence + FRB + golden GP tax/risk/trap. 30% Architecture — multi-agent + twin + audit. 20% Code — modular tests + locks. 15% Idea — sovereign auditable reasoning.

**Links:** `docs/demo/` · `docs/architecture/architecture.png` · `docs/JUDGE_QUICKSTART.md`.
