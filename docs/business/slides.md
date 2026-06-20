# FinRoot — Speaker-Ready Deck (6 slides)

> **Judging weights:** Reasoning Quality 35% · Agent Architecture 30% · Code Implementation 20% · Solution Idea 15%.
> Every slide maps to at least one axis. Numbers below are sourced from `results/metrics.json`
> (as_of_sha `8d4d03f`, n_tasks 83, 11 financial domains). Regenerate anytime with `make evals`.
> Judge reads each slide in **<20 seconds** — keep it crisp.

---

## Slide 1 — The Problem

**On-screen**
- Today's retail "AI finance" = a chatbot that calls a price API and asks an LLM to summarize.
- **No reasoning shown.** A confident sentence, no plan, no tools, no trace.
- **No risk flags.** "Buy XYZ" with no drawdown estimate, no downside scenario.
- **No citations.** Numbers without sources — stale or fabricated.
- **No memory of *you.*** Each question is independent of your goals, taxes, holdings.
- **No audit trail.** When advice goes wrong, there is nothing to replay or defend.

**Say**
Institutional investors spend millions on research teams, risk models, and compliance tooling —
retail investors get a chatbot that hallucinates stock picks. The trust gap is the real problem:
not information access, but *reasoning transparency.* A guess with no trace is not advice.

**Show**
README §"The problem" table — the six pain rows. (Optional contrast visual: left = a typical
chatbot returning a buy/sell line; right = FinRoot's chat screenshot
`docs/demo/screenshots/01_chat_portfolio.png` — kept for the demo slide, not here.)

---

## Slide 2 — Solution / Idea *(Solution Idea 15%)*

**On-screen**
- **Not a chatbot.** A multi-agent reasoning pipeline that *decides, defends, documents.*
- **Sovereign-first** — local Ollama by default; your data never leaves your machine. Cloud is opt-in.
- **The Digital Twin moat** — persistent profile of your goals, risk, horizon, taxes, holdings.
- **Built on LangChain + LangGraph** — real agent orchestration, not prompt chaining.

**Say**
FinRoot is what happens when you treat a financial agent as a *reasoning system*, not a search box.
It shows its work, flags risk, cites evidence, self-critiques, and keeps a tamper-evident audit
trail — all running locally. The Digital Twin is the moat: it learns you, so the reasoning is
context-aware, not stateless Q&A.

**Show**
README hero banner (`docs/demo/screenshots/03_trap_refusal.png`) — the one image that
communicates "sovereign, auditable, refuses to give dumb advice."

---

## Slide 3 — Architecture *(Agent Architecture 30%)*

**On-screen**
- **LangGraph Plan-and-Execute** supervisor: plan → dispatch → synthesize → critic → refine → finalize.
- **6 specialist agents:** Intent · Market · News · Portfolio · Risk · Tax.
- **12 tools in 6 groups:** market/fundamentals · news/sentiment · risk/portfolio_sim ·
  tax · macro/currency · profile/documents/watchlist.
- **4-tier memory:** Working (session) → Semantic (ChromaDB / JSON) → Digital Twin (SQLite) →
  Audit (hash-chained ledger).
- Critic and **Rooted Prudence** verifier are *in the loop*, not post-hoc.

**Say**
This isn't a single-prompt wrapper. It's a composable, observable, multi-agent system where
every component is typed (Pydantic v2), tested (pytest), ruff-clean, and audit-anchored. The
critic and the prudence verifier run on every answer before it reaches you — bad reasoning is
caught *before* it ships, not logged after.

**Show**
**`docs/architecture/architecture.png`** — full system diagram (orchestrator + agents + tools +
memory + critic + audit + LLM provider layer).

---

## Slide 4 — Reasoning Quality + FRB Results *(Reasoning Quality 35%)*

**On-screen**
- **5-axis Self-Critic:** Accuracy · Completeness · Risk Awareness · Evidence Quality · Actionability.
- **Principles verifier (Rooted Prudence):** no unsupported claims, no unhedged recommendations, confidence labels required.
- **Financial Reasoning Benchmark (FRB):** 83 tasks across 11 financial domains, deterministic graders.
- **Composite lift vs RAG: +138% (2.4×)** — FinRoot mean **0.795** vs RAG **0.334** (results/metrics.json).
- **Per-domain mean scores (FinRoot vs RAG):**
  - portfolio **0.85 vs 0.17** (+389%)
  - tax **0.87 vs 0.27** (+228%)
  - news_impact **0.77 vs 0.30** (+159%)
  - risk **0.76 vs 0.26** (+192%)

**Say**
35% of the score is reasoning quality. We built the measurement tool (FRB), the quality gate
(Self-Critic + Rooted Prudence), and the proof (benchmark lift vs a naive RAG baseline) — not
just the agent. On 83 graded queries across 11 domains, FinRoot's mean reasoning-quality score
is 0.795 versus 0.334 for a retrieve-and-summarize baseline — a composite +138% lift. The gain
is largest on the domains that demand synthesis (portfolio, tax, risk) where RAG cannot connect
the dots.

**Show**
**`docs/demo/screenshots/05_harness.png`** — the FRB harness view: composite lift vs RAG,
system comparison table, per-domain bars. Numbers are regenerated from
`results/metrics.json` (single source of truth — never hand-typed).

---

## Slide 5 — Demo *(Reasoning Quality + Architecture, live)*

**On-screen**
- **Live reasoning trace:** plan → agent dispatch → tool calls → synthesis → critic review → cited answer.
- **Trap refusal:** "Should I put my emergency fund into a hot small-cap?" → agent refuses, flags risk, offers safer alternatives.
- **Digital Twin in action:** the same query tomorrow uses *your* risk profile, horizon, tax bracket, holdings.
- **Harness delta:** run the same query through RAG baseline vs FinRoot, see the reasoning-quality gap live.

**Say**
This is not a slide — it's a working system. Ask a portfolio question and watch the reasoning
trace unfold in real time, with the critic panel on the right. Try the emergency-fund trap: a
naive chatbot would either say "yes, moonshot!" or hedge without justification. FinRoot refuses
to act on the premise, explains *why* — emergency funds exist for liquidity and tail risk, not
alpha — and offers a structured alternative plan. That refusal is the system working as designed.

**Show**
- **`docs/demo/screenshots/03_trap_refusal.png`** — the emergency-fund trap refusal card.
- Backup screens: `02_reasoning_trace.png` (live trace), `04_digital_twin.png` (profile grounding).

---

## Slide 6 — Why We Win *(all four axes)*

**On-screen**
| Axis | Weight | Where FinRoot Delivers |
|---|---:|---|
| Reasoning Quality | **35%** | 5-axis Self-Critic · Rooted Prudence verifier · FRB benchmark (+138% vs RAG) |
| Agent Architecture | **30%** | LangGraph plan-execute · 6 agents · 12 tools · 4-tier memory · typed I/O |
| Code Implementation | **20%** | Pydantic v2 · pytest taxonomy · ruff-clean · Docker · Streamlit + Typer CLI |
| Solution Idea | **15%** | Sovereign-first · Digital Twin moat · tamper-evident audit · explainability-by-design |

- **Sovereignty** — runs on your hardware, your data stays local, offline-capable Mock mode for judging.
- **Audit trail** — every decision is hash-chained; tamper-evident, not just logged.
- **Reproducibility** — deterministic Mock mode means judges can replay any demo bit-for-bit.

**Say**
We didn't build for one axis — we built a system where every architectural decision maps
directly to the scoring rubric. The 35% weapon is proof, not assertion: the FRB harness with
+138% lift over RAG on 83 graded queries is in the repo. Sovereignty, audit, and reproducibility
are not buzzwords — they're shipping features judges can run locally. FinRoot is what
institutional-grade financial reasoning looks like on an individual's own terms.

**Show**
The 4-axis table above, on screen. Close on `results/metrics.json` regenerate line —
`make evals` → numbers come out the same. *That's* the close.

---

## Appendix — Asset index (for the presenter)

| Slide | Asset |
|---:|---|
| 1 | (no image — table from README) |
| 2 | `docs/demo/screenshots/03_trap_refusal.png` (hero) |
| 3 | `docs/architecture/architecture.png` |
| 4 | `docs/demo/screenshots/05_harness.png` |
| 5 | `docs/demo/screenshots/03_trap_refusal.png` (primary) + `02_reasoning_trace.png`, `04_digital_twin.png` (backup) |
| 6 | on-screen table only |

Numbers source: `results/metrics.json` (as_of_sha `8d4d03f`, n_tasks 83, 11 domains).
Regenerate: `make evals` → updates `results/metrics.json` → re-quote any slide that
cites a metric. Do **not** hand-edit numbers in this file (FM-05/FM-12).
