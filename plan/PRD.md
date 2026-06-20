# FinRoot — Product Requirements Document (PRD)

> Living strategy doc #1 of 3. The "what" and "why". Pairs with `ARCHITECTURE.md` (the "how")
> and `EXECUTION.md` (the "when / status"). Update when scope changes; never let it drift (FM-01).

## 1. One-liner
FinRoot is a **sovereign, reasoning-first AI financial agent** that gives individual investors and
small family offices institutional-grade, explainable, auditable financial reasoning — running
locally, on the user's own terms.

## 2. The problem
Individual investors lack integrated financial intelligence that combines market analysis, risk
assessment, tax optimization, and *personalized, transparent reasoning* in one trustworthy system.
Today's options each fail a different way:
- **Robo-advisors** — opaque, no reasoning shown, rigid, your data leaves your control.
- **LLM chatbots** — no durable memory, no risk awareness, prone to hallucinated figures.
- **Human advisors** — expensive, not 24/7, not auditable, not scalable.

The gap: nobody gives the individual **reasoning quality + transparency + control** together.

## 3. Target user
Primary: an informed individual investor or small family office (India-first context: rupee
realities, Indian tax regime, family goals) who wants institutional-grade reasoning with full
transparency and data control. Secondary: the SCALE judges evaluating reasoning quality live.

## 4. Objectives (what success looks like)
- O1. The agent **reasons** through decisions (decompose → evidence → scenario → risk → recommend
  → verify), not just answers. It shows its work.
- O2. Every recommendation is **explainable, risk-aware, cited, and confidence-labeled**; it can
  say "insufficient evidence — do not act yet".
- O3. Every recommendation has a **complete, replayable, tamper-evident audit trail**.
- O4. Runs **sovereign / local-first** (Ollama) with an offline Mock mode for judging.
- O5. Reasoning quality is **measurable and proven** to beat a RAG baseline (the FRB harness).

## 5. Novelty (beyond the PS common examples)
The PS lists single-function examples (stock advisor, credit advisor, news summarizer). FinRoot
*integrates all three* and adds a new category — a **trustworthy financial reasoning partner**:
1. **Self-Critic reasoning loop** — recommendations scored on 5 axes and refined before delivery.
2. **Financial Digital Twin** — reasons over the user's evolving state, not just the message.
3. **Rooted Prudence Principles** — a verifier enforcing timeless wealth discipline (long-term,
   downside-first, no overclaiming) — *artha aligned with dharma*.
4. **Multi-objective + temporal reasoning** — holds competing goals (growth vs safety vs tax) and
   reasons explicitly about short- vs long-term trade-offs.
5. **Hash-chained audit trail** — institutional-grade accountability for a consumer tool.
6. **Sovereignty** — local models, local data, no blind closed-API reliance.

## 6. Core capabilities (the feature set)
| # | Capability | Notes |
|---|---|---|
| C1 | Portfolio reasoning | allocation review, concentration risk, rebalancing, downside scenarios |
| C2 | Risk analysis | VaR, Sharpe, beta, max drawdown, stress tests |
| C3 | Market & news reasoning | event summarization, impact analysis, sentiment with evidence, portfolio relevance |
| C4 | Tax reasoning (India-first) | deterministic capital-gains / slab engine, deduction limits, FY-end actions |
| C5 | Cashflow & liquidity | emergency-fund sufficiency, goal-based savings, runway |
| C6 | Credit & debt reasoning | debt burden, repayment sequencing, interest-cost prioritization |
| C7 | Scenario simulation | Monte-Carlo portfolio paths, bull/base/bear, sensitivity |
| C8 | Explainable decision support | rationale, alternatives, confidence, risk notes, "do not act yet" |
| C9 | Memory / Digital Twin | remembers goals, risk tolerance, horizon, holdings, tax bracket |
| C10 | Audit & export | full reasoning trace export, tamper-evident |

## 7. Non-goals (OUT — see docs/SCOPE_GUARD.md)
- NOT executing trades or moving money (decision-support only; r5 blast radius — blocked).
- NOT multi-tenant SaaS, billing, or auth portals (single-user / family scope).
- NOT real-time HFT or tick-level trading signals.
- NOT a replacement for a licensed advisor (explicitly disclaimed).

## 8. Success metrics (acceptance — single source: results/metrics.json + evals/reports/)
| Metric | Target | Stretch |
|---|---|---|
| FRB reasoning-quality lift vs RAG baseline | ≥ +40% composite | ≥ +55% |
| FRB capability pass@5 (per domain) | ≥ 50% → graduate to regression | ≥ 70% |
| Regression suite pass^3 | ≥ 80% | ≥ 90% |
| Hallucinated financial figures (uncited numbers) | 0 in graded runs | 0 |
| Cited-claim rate on numeric outputs | 100% | 100% |
| Mock-mode demo latency (judge path) | < 2s/query | < 1s |
| Audit completeness (every rec has full trace) | 100% | 100% |

## 9. Risks (register — mitigations in ARCHITECTURE + HALL_OF_SHAME)
| Risk | Mitigation |
|---|---|
| Hallucinated figures | tool-only numbers + cited-claim grader (FM-11) |
| Self-Critic rubber-stamping | class-balanced evals with bad answers it must catch |
| Live API flakiness during demo | Mock mode default; cache + graceful degradation |
| Scope creep eats the deadline | SCOPE_GUARD + BACKLOG; waves shipped one at a time |
| Local model too weak for reasoning | provider cascade; Groq fallback; FRB measures the trade-off |
| Tax-rule inaccuracy | one deterministic source, unit-tested against known cases |

## 10. Constraints
- **Deadline-driven competition** — ship a working end-to-end demo path early; polish later.
- **Sovereign-first** — must run offline (Mock) and locally (Ollama) with no keys.
- **LangChain-native** — judged on effective use of LangChain agents/chains/tools/memory.
- **Reasoning quality is 35%** — the single most important investment of effort.

## 11. Open questions (track in docs/decisions/ as resolved)
- Live data providers to wire first (yfinance is keyless → default; AlphaVantage/NewsAPI optional).
- Depth of Indian tax engine for v1 (LTCG/STCG equity + 80C is the MVP slice).
