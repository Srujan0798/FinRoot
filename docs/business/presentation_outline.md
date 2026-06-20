# FinRoot — 6-Slide Deck Outline

> Judges target: **Reasoning Quality 35% · Agent Architecture 30% · Code Implementation 20% · Solution Idea 15%**
> Every slide maps to at least one axis.

---

## Slide 1 — The Problem

**Title:** Individual Investors Are Flying Blind

**Talking points:**
- Institutional investors spend millions on research teams, risk models, and compliance tooling — retail investors get a chatbot that hallucinates stock picks.
- Current AI finance tools are wrappers: no reasoning trace, no risk flags, no audit trail. When they're wrong, you don't know why.
- The trust gap is the real problem — not information access, but *reasoning transparency*.
- Regulatory pressure (MiFID II, SEC guidance) demands explainability; retail tools ignore it entirely.

**Visual:** Split-screen: left = Bloomberg terminal with multi-analyst workflow; right = a typical chatbot giving a stock tip with no evidence.

**So what:** There's no product that gives an individual investor institutional-grade, explainable, auditable financial reasoning on their own terms. Until now.

---

## Slide 2 — The Solution / Idea *(Solution Idea 15%)*

**Title:** FinRoot — A Sovereign, Reasoning-First Financial Agent

**Talking points:**
- Not a chatbot. A multi-agent reasoning pipeline that *shows its work*, flags risk, cites evidence, self-critiques, and keeps a tamper-evident audit trail.
- **Sovereign-first:** runs locally via Ollama by default — your financial data never leaves your machine. Cloud providers (OpenAI, Groq) available but optional.
- **The Digital Twin moat:** a persistent financial profile that learns your risk tolerance, goals, tax situation, and portfolio over time — not stateless Q&A.
- Built on LangChain + LangGraph: real agent orchestration, not prompt chaining.

**Visual:** Architecture thumbnail (full diagram on Slide 3) with the "user → reasoning pipeline → cited, risk-flagged answer" flow highlighted.

**So what:** FinRoot is what happens when you treat a financial agent as a *reasoning system*, not a search box.

---

## Slide 3 — Agent Architecture *(Agent Architecture 30%)*

**Title:** 6 Agents · 12 Tools · 4-Tier Memory — One Orchestrated Pipeline

**Talking points:**
- **LangGraph Plan-and-Execute:** the orchestrator decomposes a query into a plan, dispatches to specialist agents, synthesizes, and routes through the critic before returning.
- **6 specialist agents:** Portfolio, Risk, Market, News, Tax, Intent — each with domain-specific tools and typed Pydantic outputs.
- **12 tools:** market data, fundamentals, sentiment, news search, currency conversion, portfolio simulation, tax calculation, risk metrics, watchlist, user profile, document analysis, macro indicators.
- **4-tier memory:** Working (session) → Semantic (long-term vector) → Digital Twin (persistent user model) → Audit (tamper-evident hash chain).
- The critic (5-axis self-evaluation) and principles verifier are *in the loop*, not post-hoc.

**Visual:** Full architecture diagram — `docs/architecture/architecture.mmd` rendered as PNG.

**So what:** This isn't a single-prompt wrapper. It's a composable, observable, multi-agent system — and every component is typed, tested, and auditable.

---

## Slide 4 — Reasoning Quality + FRB Results *(Reasoning Quality 35%)*

**Title:** The 5-Axis Self-Critic + Financial Reasoning Benchmark

**Talking points:**
- **5-axis critic:** every answer is scored on Accuracy, Completeness, Risk Awareness, Evidence Quality, and Actionability — with pass/fail thresholds.
- **Principles verifier:** checks answers against financial reasoning principles (no unsupported claims, no unhedged recommendations, confidence labels required).
- **Financial Reasoning Benchmark (FRB):** 83 graded tasks across 11 financial domains scored by deterministic graders — measures reasoning quality, not just answer correctness.
- **Measured lift:** FinRoot **0.795** mean score vs naive RAG **0.334** — **2.4× lift (+138%)**, pass@1 **0.193 vs 0.289**, across 11 financial domains (general 0.92, tax 0.87, portfolio 0.85, credit 0.85).
- **FRB results:** FinRoot's reasoning pipeline scores significantly higher than a naive RAG baseline on reasoning quality. *(Numbers from `results/metrics.json` at `as_of_sha = 8d4d03f`. Regenerate via `make evals`.)*
- The critic *catches bad answers before they reach the user* — not after-the-fact logging.

**Visual:** Bar chart comparing FinRoot vs RAG baseline on the 5 axes; table showing critic pass/fail rates on FRB queries.

**So what:** 35% of the score is reasoning quality. We built the measurement tool (FRB), the quality gate (critic), and the proof (benchmark results) — not just the agent.

---

## Slide 5 — Live Demo

**Title:** See It Think: Live Reasoning Trace + Trap Refusal

**Talking points:**
- Ask a portfolio question → watch the reasoning trace unfold: plan → agent dispatch → tool calls → synthesis → critic review → final answer with citations.
- **Trap refusal:** ask "Should I buy TSLA right now?" → the agent refuses to give a buy/sell recommendation, explains why, and offers risk analysis and evidence instead — exactly what a responsible system should do.
- **Digital Twin:** the agent remembers your risk profile and portfolio from previous sessions — context-aware reasoning, not stateless.
- **Harness:** run the same query through RAG baseline vs FinRoot, show the delta in reasoning quality scores live.

**Visual:** Screen recording of the Streamlit UI showing the reasoning trace expanding in real time, with the critic panel on the right.

**So what:** This is not a slide. It's a working system. The reasoning is real, the refusal is real, the audit trail is real.

---

## Slide 6 — Why We Win

**Title:** The 4-Axis Scorecard — Built to Win Every Category

**Talking points:**

| Scoring Axis | Weight | Where FinRoot Delivers |
|---|---|---|
| Reasoning Quality | 35% | 5-axis critic, principles verifier, FRB benchmark, harness delta |
| Agent Architecture | 30% | LangGraph plan-execute, 6 agents, 12 tools, 4-tier memory, typed I/O |
| Code Implementation | 20% | Pydantic v2, pytest, ruff, Docker, Streamlit + CLI, clean module structure |
| Solution Idea | 15% | Sovereign-first, Digital Twin moat, audit trail, explainability-by-design |

- **Sovereignty:** runs on your hardware, your data stays local, offline-capable with Mock mode for judging.
- **Audit trail:** every decision is hash-chained and tamper-evident — not just logging, but provable integrity.
- **Reproducibility:** deterministic Mock mode means judges can reproduce any demo exactly.

**Visual:** 4-axis radar chart showing FinRoot's coverage across all scoring dimensions.

**So what:** We didn't build for one axis. We built a system where every architectural decision maps directly to the scoring rubric — and it works.
