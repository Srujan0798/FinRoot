# FinRoot — Submission Checklist (SCALE ML Club — PS-1)

> **"Build an AI Agent for Finance."** This document maps every PS-1 ask to the exact
> FinRoot component, file, or runnable artifact that satisfies it. Everything here is
> reproducible offline (Mock mode, no keys).

---

## 1. PS-1 → FinRoot mapping

| PS-1 ask | What it means | FinRoot answer | Where to look |
|---|---|---|---|
| **LLM reasoning** | Agent uses an LLM to reason, not just retrieve | LangGraph Plan-and-Execute loop over 6 specialized agents; Self-Critic refine; LLM-provider abstraction (Mock / Ollama / Groq / OpenAI) | `src/finroot/workflows/orchestrator.py` · `src/finroot/agents/` · `src/finroot/llm/` · [`docs/architecture/architecture.mmd`](architecture/architecture.mmd) |
| **External tools / APIs** | Agent calls real tools, not a single prompt | 12 tools across 6 functional groups (market, fundamentals, news/sentiment, risk+portfolio_sim, deterministic tax, macro/currency, profile/documents/watchlist) — all with cache, rate-limit, loud-fail, audit hooks | `src/finroot/tools/` (12 modules) |
| **Memory** | Agent retains context across turns and across sessions | 4-tier memory: working context · semantic (ChromaDB / JSON) · **Digital Twin** (SQLite — your goals/risk/horizon/holdings/tax-bracket) · audit | `src/finroot/memory/working.py` · `semantic.py` · `digital_twin.py` · `src/finroot/audit/` |
| **Agent workflows** | Multi-step, branching, reflective — not a one-shot prompt | Plan → Execute loop → Synthesize → **Self-Critic (5-axis)** → **Rooted Prudence verifier** → Finalize → Audit emit, with refine edges | `src/finroot/reasoning/critic.py` · `src/finroot/reasoning/prudence.py` · [`docs/decisions/0003-langgraph-plan-and-execute.md`](decisions/0003-langgraph-plan-and-execute.md) · [`0005-five-axis-self-critic.md`](decisions/0005-five-axis-self-critic.md) |
| **Real-time** | Agent reacts to fresh market / news data | News & sentiment tools, market data tools, macro/currency — each emit a `retrieved_at` timestamp in their `Citation` so freshness is auditable, not asserted | `src/finroot/tools/news.py` · `sentiment.py` · `market.py` · `macro.py` |
| **Accurate / contextual / actionable** | Numbers grounded, personalized, and ready to act on | Every answer carries: a confidence label, a risk band, citations to the tool + timestamp, **and** Digital-Twin context (so advice is grounded in *your* state, not generic). The 5-axis critic refuses to ship low scores and the Rooted Prudence verifier blocks dangerous recommendations | `src/finroot/reasoning/critic.py` · `src/finroot/reasoning/prudence.py` · `src/finroot/memory/digital_twin.py` |

---

## 2. Why FinRoot is a complete PS-1 submission (not a chatbot wrapper)

- **Reasoning that you can replay.** Every step is in a hash-chained audit trail — when
  advice is wrong, you can show *why* and *where*. ([`docs/decisions/0007-hash-chained-audit-trail.md`](decisions/0007-hash-chained-audit-trail.md))
- **Reasoning that you can *measure*.** The FRB benchmark compares Baseline-RAG,
  Single-Agent, and full FinRoot on the same tasks and reports pass@k + composite lift.
  Single source of truth: `results/metrics.json`. ([`evals/README.md`](../../evals/README.md))
- **Reasoning that respects your autonomy.** Sovereign-first: runs locally, no telemetry,
  no vendor lock-in. ([`docs/decisions/0006-sovereign-first-mock-default.md`](decisions/0006-sovereign-first-mock-default.md))
- **Reasoning with a Digital Twin.** Advice is grounded in your goals, risk tolerance,
  horizon, holdings, tax bracket — never generic. ([`docs/decisions/0004-four-tier-memory-and-digital-twin.md`](decisions/0004-four-tier-memory-and-digital-twin.md))

---

## 3. Linked artifacts

| What | Path |
|---|---|
| Hero README (judge entry point) | [`README.md`](../../README.md) |
| Architecture diagram (Mermaid) | [`docs/architecture/architecture.mmd`](architecture/architecture.mmd) |
| Demo script (7-minute, click-by-click narration) | [`docs/business/7_minute_demo_script.md`](business/7_minute_demo_script.md) |
| Demo transcripts (4 showcase queries, offline-capturable) | [`docs/demo/transcript_1_portfolio.md`](demo/transcript_1_portfolio.md) · [`docs/demo/transcript_2_tax_with_number.md`](demo/transcript_2_tax_with_number.md) · [`docs/demo/transcript_3_news_impact.md`](demo/transcript_3_news_impact.md) · [`docs/demo/transcript_4_trap_question.md`](demo/transcript_4_trap_question.md) |
| Executive summary (1 page) | [`docs/business/executive_summary.md`](business/executive_summary.md) |
| Presentation outline (6 slides) | [`docs/business/presentation_outline.md`](business/presentation_outline.md) |
| Architecture decision records (8 ADRs, MADR format) | [`docs/decisions/0001-tier-and-archetype.md`](decisions/0001-tier-and-archetype.md) → [`0008-deterministic-tax-engine.md`](decisions/0008-deterministic-tax-engine.md) |
| Reasoning-quality proof (FRB harness) | [`evals/README.md`](../../evals/README.md) · `results/metrics.json` |
| How the dual-tier build works | [`HOW_TO_RUN.md`](../../HOW_TO_RUN.md) · [`HIERARCHY.md`](../../HIERARCHY.md) |

---

## 4. Demo reproduction (judge-safe, offline)

You can reproduce the entire demo **without API keys, without the internet**, using Mock mode.

### 4.1 Run the CLI in Mock mode

```bash
pip install -e .[ui]
python -m src.interface.cli --mock \
  "Should I rebalance my 70/30 equity portfolio before FY-end?"
```

Expected: a multi-section answer (`summary`, `analysis`, `confidence`, risk band) with
citations to the tools that produced each number, plus a reasoning trace.

### 4.2 Run the dark Streamlit UI

```bash
streamlit run src/interface/ui/app.py
# open http://localhost:8501
```

Ask the showcase queries from the demo script (Beat 2–6) and inspect the Reasoning Trace panel.

### 4.3 Reproduce / regenerate the eval table

```bash
make evals                      # runs the FRB harness → results/metrics.json + evals/reports/
python scripts/run_evals.py --mock --task 001    # single task, fast
```

After `make evals`, `results/metrics.json` exists and the **FRB Results** table in the README
should be regenerated from it (do not hand-edit — FM-12).

### 4.4 Capture offline screenshots / video

```bash
python scripts/capture_demo.py        # writes docs/demo/transcript_*.md for 4 showcase queries
```

The capture script writes formatted outputs (answer + reasoning trace + critic verdict +
citations) to `docs/demo/transcript_*.md`. These are the source for static screenshots and
the offline narration script.

### 4.5 Build the submission zip

```bash
bash scripts/make_submission.sh       # produces finroot-submission.zip (no secrets, no caches)
```

---

## 5. Trust guarantees

- **No fabricated numbers.** Every figure in an answer carries a `Citation` (tool + timestamp).
  Missing required input fails loud (FM-11).
- **No silent failures.** No bare `except:`; fallbacks log loudly (FM-11).
- **No state drift.** `HANDOFF.md` / `plan/EXECUTION.md` are the source of truth (FM-01).
- **No parallel collisions.** Each wave's tasks have disjoint write-sets (FM-13).
- **No secrets committed.** `.env.example` shows placeholders; `.dockerignore` excludes `.env*`
  and DB caches (FM-07).

---

*Last regenerated as part of wave-8 deploy/docs. If you are reading this and `results/metrics.json`
is absent, run `make evals` and re-render the FRB table — do not hand-fill numbers.*