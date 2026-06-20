# FinRoot — 7-Minute Demo Script

> Timed, click-by-click narration for judges. Each beat: **[mm:ss] — what to click — what to say**.
> Built for SCALE ML Club PS-1 judging. Covers all 4 scoring axes.

---

## Beat 1 — [0:00] Hook

**Click:** Open the FinRoot Streamlit app (dark UI loads).

**Say:**
"Every year, millions of investors make decisions based on black-box advice — no reasoning shown, no evidence cited, no audit trail. When things go wrong, they can't explain why. FinRoot changes that. We built a sovereign, reasoning-first AI financial agent that *shows its work*, flags risk, cites every number, and keeps a tamper-evident audit trail — all running locally on your machine."

**Reliability note:** If the UI doesn't load, run `docker compose up -d` or `streamlit run src/interface/ui/app.py`. If Streamlit is slow, hard-refresh the browser.

---

## Beat 2 — [0:45] Ask a Portfolio Question

**Click:** Type into the Chat input: *"What is my current portfolio allocation and risk level?"*

**Say:**
"Let's ask a real question. Watch the answer card — it shows a confidence label, a risk assessment, and every number is backed by a citation to the tool that produced it. No hallucinated figures. The Digital Twin already knows my holdings, goals, and risk tolerance."

**What to show:**
- Answer card appears with `summary`, `analysis`, `confidence` badge.
- Citations list (source tool + retrieved_at timestamp).
- Risk band displayed.

**Reliability note:** If answer() returns empty or times out, the Mock provider may not be active. Check `FINROOT_LLM_PROVIDER=mock` in the environment. Fall back to showing a pre-captured transcript from `docs/demo/transcript_1_portfolio.md`.

---

## Beat 3 — [2:00] Open the Reasoning Trace

**Click:** Expand the Reasoning Trace panel (or switch to the Trace tab).

**Say:**
"This is where FinRoot earns the 35% Reasoning Quality score. Every step the agent took is visible: the planner's decomposition, the tools it called, the data each tool returned, and — critically — the 5-axis critic verdict. The critic scores the answer on factual accuracy, completeness, risk awareness, citation quality, and actionability. If any axis fails, the agent self-corrects before showing you the answer."

**What to show:**
- Step-by-step trace: `planner → market_data → portfolio_twin → tax_engine → synthesizer → critic`.
- Critic 5-axis verdict (the "35% moment").
- Each tool output with its source.

**Reliability note:** If the trace panel is empty, the `build_trace()` function may not have wired. Check `state.audit_events` is populated. Show `docs/demo/transcript_1_portfolio.md` trace section as fallback.

---

## Beat 4 — [3:30] The Trap Question

**Click:** Type into Chat: *"I want to put my emergency fund into this high-growth small-cap stock I heard about."*

**Say:**
"Now the real test. This is a dangerous question — moving an emergency fund into a volatile small-cap violates basic financial principles. Watch what happens."

**What to show:**
- The Prudence Verifier fires — `PrudentialVerifier.verify()` flags the advice.
- The agent responds with **LOW confidence** and a caution: *"do not act yet."*
- Specific violated principles listed (e.g., "Emergency fund preservation", "Concentration risk").
- The answer explicitly says: *"This advice may not be suitable — verify against your full financial picture."*

**Reliability note:** If the verifier doesn't fire, check that `finroot.reasoning.principles` is importable. If the trap question gets a confident answer instead of a refusal, the verifier may need the `FINROOT_LLM_PROVIDER=mock` env var. Show `docs/demo/transcript_4_trap.md` as fallback.

---

## Beat 5 — [4:30] Digital Twin Tab

**Click:** Switch to the Digital Twin tab in the UI.

**Say:**
"FinRoot doesn't just answer generic questions — it knows *you*. The Digital Twin holds your holdings, goals, risk tolerance, and constraints. When I ask about my portfolio, it references my actual positions — HDFC FD, ICICI balanced fund, SBI debt fund, PPF. It knows I'm conservative with a 10-year horizon. This personalization means the advice is contextual, not generic."

**What to show:**
- Twin profile: name, age, risk tolerance, investment horizon.
- Holdings list with real values.
- Goals and constraints.

**Reliability note:** If the twin tab is empty, the `twin_profiles.json` sample may not have loaded. Check `data/samples/twin_profiles.json` exists. Restart the app to re-seed.

---

## Beat 6 — [5:15] Harness Tab — FRB vs RAG

**Click:** Switch to the Harness tab. Run the FRB (FinRoot Reasoning Bank) evaluation.

**Say:**
"Here's the measured proof. We run the same financial questions through two pipelines: a standard RAG baseline and FinRoot's full reasoning pipeline. The FRB harness scores both on our 5-axis rubric. Watch the delta — FinRoot's multi-agent reasoning with self-critique consistently outperforms the RAG baseline on reasoning quality, risk awareness, and citation completeness."

**What to show:**
- FRB evaluation results table.
- Score delta: FinRoot vs RAG baseline.
- Key metric: reasoning quality improvement.

**Reliability note:** If the harness tab shows no data, run `PYTHONPATH=src python3 -m finroot.evaluation.frb_runner` to populate results. If that fails, show the static results from `results/metrics.json`.

---

## Beat 7 — [6:15] Audit Trail

**Click:** Switch to the Audit Trail tab (or expand the audit section).

**Say:**
"Sovereignty and trust. Every action FinRoot takes is logged in a tamper-evident hash chain — each entry includes the SHA-256 hash of the previous entry. If anyone tries to alter a past event, the chain breaks and we detect it. And because everything runs locally — Mock mode by default — your financial data never leaves your machine. No API keys required. No cloud dependency. Full sovereignty."

**What to show:**
- Audit events list with `seq`, `type`, `hash`, `prev_hash`.
- Hash chain verification: `trail.verify_chain() === True`.
- Offline/Mock mode indicator.

**Reliability note:** If the audit tab is empty, the in-memory audit trail may not have persisted. Check the temp file path. Show the audit events from the most recent `answer()` call as fallback.

---

## Beat 8 — [6:45] Wrap — Why We Win

**Click:** Return to the main view. Show the scoring-criteria mapping.

**Say:**
"Let's map to the judging criteria:
- **Reasoning Quality (35%):** The 5-axis critic, the visible trace, the self-correction loop — every recommendation shows its work.
- **Agent Architecture (30%):** Six specialized agents orchestrated by LangGraph, four-tier memory, hash-chained audit trail.
- **Code Implementation (20%):** Pydantic v2 at every boundary, ruff-clean, 100% typed, tests for every module.
- **Solution Idea (15%):** Sovereign-first, offline-default, Digital Twin personalization — a financial agent you can actually trust.

FinRoot isn't a chatbot wrapper. It's institutional-grade financial reasoning, locally, on your terms."

**Reliability note:** If any section of the demo fails, fall back to the pre-captured transcripts in `docs/demo/`. Each transcript contains the full answer card, trace, critic verdict, and citations — formatted for screenshots.

---

## Quick Reference — Demo Flow

| Time | Beat | Key Action | Scoring Axis |
|------|------|------------|--------------|
| 0:00 | Hook | Open app | Idea (15%) |
| 0:45 | Portfolio Q | Ask in Chat | Reasoning (35%) |
| 2:00 | Reasoning Trace | Expand trace | Reasoning (35%) |
| 3:30 | Trap Question | Ask dangerous Q | Architecture (30%) |
| 4:30 | Digital Twin | Show twin tab | Idea (15%) |
| 5:15 | Harness | Run FRB eval | Architecture (30%) |
| 6:15 | Audit Trail | Show hash chain | Architecture (30%) |
| 6:45 | Wrap | Criteria mapping | All axes |

## Pre-Captured Transcripts

For screenshots or fallback, run:
```bash
PYTHONPATH=src python3 scripts/capture_demo.py
```

This produces `docs/demo/transcript_*.md` files with formatted answer cards, traces, and citations.
