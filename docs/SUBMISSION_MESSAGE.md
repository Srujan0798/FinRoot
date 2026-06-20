# SCALE ML Club PS-1 — Submission Message

> Ready-to-paste message for organizers. ≤ 250 words.

---

**FinRoot — Sovereign, Reasoning-First AI Financial Agent**

FinRoot gives individual investors institutional-grade, explainable, auditable financial reasoning — locally and on their own terms. It is not a chatbot wrapper; it is a 6-agent LangGraph reasoning pipeline that shows its work, flags risk, cites evidence, self-critiques, and keeps a tamper-evident audit trail.

**Repo:** https://github.com/Srujan0798/FinRoot

### Run it in 30 seconds

**Docker (recommended):**

```bash
docker compose up --build
# open http://localhost:8501
```

**CLI (no Docker):**

```bash
pip install -e .[ui]
PYTHONPATH=src python -m interface.cli --mock "Should I rebalance my 70/30 portfolio before FY-end?"
```

### Judging-criteria scorecard

| Weight | Criterion | Where FinRoot delivers |
|---:|---|---|
| 35% | Reasoning Quality | 5-axis Self-Critic + Rooted Prudence verifier + FRB harness proving +128% lift over RAG baseline (`evals/`, `results/metrics.json`) |
| 30% | Agent Architecture | LangGraph Plan-and-Execute · 6 specialized agents · 12 tools · 4-tier memory + Digital Twin · hash-chained audit trail |
| 20% | Code Implementation | Modular `src/finroot/` · Pydantic v2 · pytest taxonomy · ruff-clean · Dockerized |
| 15% | Solution Idea | Sovereign, auditable reasoning over your financial Digital Twin — long-term-thinking-first, downside-aware, locally runnable |

### FRB headline

**FinRoot mean score: 0.778 across 83 tasks across 11 financial domains — +128.5% composite lift vs RAG baseline.**
*(as_of_sha: a335c45 · `results/metrics.json`)*

### Links

- **Demo video:** `<your-video-link>`
- **Screenshots:** [`docs/demo/screenshots/`](demo/screenshots/)
- **Architecture diagram:** [`docs/architecture/architecture.png`](architecture/architecture.png)
