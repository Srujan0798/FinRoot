# FinRoot — Demo Video Shot List + Narration

> Operational scene-by-scene recording guide. Target: **3–5 min**, tight, professional.
> Companion to `7_minute_demo_script.md` — that script is the *why*; this is the *how*.

---

## Pre-Record Checklist

| # | Check | Command / Action |
|---|-------|-----------------|
| 1 | Terminal font size ≥ 16 pt | iTerm2 → Profiles → Text → 16pt |
| 2 | Browser window 1920×1080 | Chrome → View → Actual Size; resize window |
| 3 | Clean Digital Twin state | `rm -f data/digital_twin.db` |
| 4 | Mock provider active | `export FINROOT_LLM_PROVIDER=mock` |
| 5 | App running | `PYTHONPATH=src streamlit run src/interface/ui/app.py` |
| 6 | Close all other tabs / notifications | Eliminate distractions |
| 7 | Screen recorder ready (OBS / QuickTime) | 1920×1080, 30 fps, system audio off |

**Record in 2 takes:** Take 1 is a full run-through to catch timing issues. Take 2 is the final — restart the app after `rm -f data/digital_twin.db` for a clean slate.

---

## Shot List

### Scene 1 — Cold Open (10 s)

| Field | Detail |
|-------|--------|
| **On-screen** | Dark UI landing page; FinRoot logo visible |
| **Action** | Click the app tab; let the dark UI render |
| **Say (verbatim)** | "Every year, millions of investors get black-box advice — no reasoning, no evidence, no audit trail. FinRoot changes that: a sovereign AI financial agent that shows its work, cites every number, and runs entirely on your machine." |
| **Fallback** | If UI fails to load, run `docker compose up -d` or `streamlit run src/interface/ui/app.py`. |

---

### Scene 2 — Launch & Offline Badge (15 s)

| Field | Detail |
|-------|--------|
| **On-screen** | Chat tab open; "Mock" provider badge visible in sidebar |
| **Action** | Point cursor to the Mock/offline badge in the sidebar |
| **Say (verbatim)** | "FinRoot runs offline by default — no API keys, no cloud calls. The Mock provider badge confirms we're fully local. This is sovereignty by design." |
| **Fallback** | If badge not visible, check `FINROOT_LLM_PROVIDER=mock` in env. |

---

### Scene 3 — Portfolio Query → Answer Card (30 s)

| Field | Detail |
|-------|--------|
| **On-screen** | Chat tab; answer card with summary, confidence badge, risk band, citations |
| **Screenshot ref** | `docs/demo/screenshots/01_chat_portfolio.png` |
| **Action** | Click Chat input → type: `What is my current portfolio allocation and risk level?` → press Enter |
| **Say (verbatim)** | "Let's ask a real question. Watch the answer card — confidence label, risk assessment, and every number backed by a citation to the tool that produced it. No hallucinated figures. The Digital Twin already knows my HDFC FD, ICICI balanced fund, SBI debt fund, and PPF." |
| **Fallback** | If answer times out, check `FINROOT_LLM_PROVIDER=mock`. Show `docs/demo/transcript_1_portfolio.md`. |

---

### Scene 4 — Reasoning Trace Tab (40 s) — *the 35% moment*

| Field | Detail |
|-------|--------|
| **On-screen** | Reasoning Trace tab; step-by-step planner→tools→critic flow |
| **Screenshot ref** | `docs/demo/screenshots/02_reasoning_trace.png` |
| **Action** | Click "Reasoning Trace" tab → scroll through each step |
| **Say (verbatim)** | "This is where FinRoot earns the 35% Reasoning Quality score. Every step is visible: the planner's decomposition, the tools it called, the data each tool returned — and critically, the 5-axis critic verdict. It scores on factual accuracy, completeness, risk awareness, citation quality, and actionability. If any axis fails, the agent self-corrects before showing you the answer." |
| **Fallback** | If trace empty, check `state.audit_events` population. Show `docs/demo/transcript_1_portfolio.md` trace section. |

---

### Scene 5 — Tax Query with ₹ Amount (25 s)

| Field | Detail |
|-------|--------|
| **On-screen** | Chat tab; answer card showing ₹10,400 tax figure with citation |
| **Action** | Click Chat input → type: `How much tax will I pay on my FD interest this year?` → press Enter |
| **Say (verbatim)** | "Let's try a tax question. Watch for the cited ₹10,400 result — every rupee traced to the tax engine tool call with a retrieval timestamp. No invented numbers." |
| **Fallback** | If tax figure not shown, check `finroot.tools.tax_engine` mock data. Show pre-captured transcript. |

---

### Scene 6 — Emergency Fund Trap (40 s) — *the wow moment*

| Field | Detail |
|-------|--------|
| **On-screen** | Chat tab; LOW confidence badge, caution response, violated principles listed |
| **Screenshot ref** | `docs/demo/screenshots/03_trap_refusal.png` |
| **Action** | Click Chat input → type: `I want to put my emergency fund into this high-growth small-cap stock I heard about.` → press Enter |
| **Say (verbatim)** | "Now the real test. Moving an emergency fund into a volatile small-cap violates basic financial principles. Watch — the Prudence Verifier fires, the agent flags this with LOW confidence, and tells me: do not act yet. It lists the violated principles — emergency fund preservation, concentration risk — and says this advice may not be suitable. That's responsible AI." |
| **Fallback** | If verifier doesn't fire, check `FINROOT_LLM_PROVIDER=mock` and `finroot.reasoning.principles` import. Show `docs/demo/transcript_4_trap.md`. |

---

### Scene 7 — Digital Twin Tab (20 s)

| Field | Detail |
|-------|--------|
| **On-screen** | Digital Twin tab; profile with holdings, goals, risk tolerance |
| **Screenshot ref** | `docs/demo/screenshots/04_digital_twin.png` |
| **Action** | Click "Digital Twin" tab → scroll through profile and holdings |
| **Say (verbatim)** | "FinRoot knows you. The Digital Twin holds my holdings, goals, risk tolerance — HDFC FD, ICICI balanced fund, SBI debt fund, PPF. Conservative profile, 10-year horizon. Advice is personal, not generic." |
| **Fallback** | If twin empty, check `data/samples/twin_profiles.json` exists. Restart app to re-seed. |

---

### Scene 8 — Harness Tab — FRB vs RAG (30 s)

| Field | Detail |
|-------|--------|
| **On-screen** | Harness tab; FRB evaluation results table with score deltas |
| **Screenshot ref** | `docs/demo/screenshots/05_harness.png` |
| **Action** | Click "Harness" tab → point to score delta |
| **Say (verbatim)** | "Measured proof. We run the same questions through a standard RAG baseline and FinRoot's full reasoning pipeline. The FRB harness scores both on our 5-axis rubric. Watch the delta — multi-agent reasoning with self-critique consistently outperforms on reasoning quality, risk awareness, and citation completeness." |
| **Fallback** | If no data, run `PYTHONPATH=src python3 -m finroot.evaluation.frb_runner`. Show `results/metrics.json`. |

---

### Scene 9 — Audit Trail / Sovereignty Close (20 s)

| Field | Detail |
|-------|--------|
| **On-screen** | Audit Trail tab; event list with seq, type, hash, prev_hash |
| **Action** | Click "Audit Trail" tab → scroll through hash chain entries |
| **Say (verbatim)** | "Sovereignty and trust. Every action is logged in a tamper-evident hash chain — SHA-256 hash of the previous entry. Alter anything and the chain breaks. Everything runs locally. No API keys. No cloud dependency. Full sovereignty." |
| **Fallback** | If audit empty, check temp file persistence. Show events from most recent `answer()` call. |

---

### Scene 10 — Outro — Scorecard + Repo Link (15 s)

| Field | Detail |
|-------|--------|
| **On-screen** | Return to main view; scoring criteria overlay or slide |
| **Action** | Switch back to Chat tab or show criteria slide |
| **Say (verbatim)** | "Four axes: Reasoning Quality — 35% — the 5-axis critic and visible trace. Agent Architecture — 30% — six agents, LangGraph orchestration, hash-chained audit. Code Implementation — 20% — Pydantic v2, ruff-clean, fully typed. Solution Idea — 15% — sovereign-first, offline-default, Digital Twin personalization. FinRoot: institutional-grade financial reasoning, locally, on your terms." |
| **Fallback** | N/A — static content. |

---

## Scene Summary

| # | Scene | Duration | Key Metric |
|---|-------|----------|------------|
| 1 | Cold Open | 10 s | Idea (15%) |
| 2 | Launch & Offline Badge | 15 s | Idea (15%) |
| 3 | Portfolio Query | 30 s | Reasoning (35%) |
| 4 | Reasoning Trace | 40 s | Reasoning (35%) |
| 5 | Tax Query (₹10,400) | 25 s | Reasoning (35%) |
| 6 | Emergency Fund Trap | 40 s | Architecture (30%) |
| 7 | Digital Twin | 20 s | Idea (15%) |
| 8 | Harness (FRB vs RAG) | 30 s | Architecture (30%) |
| 9 | Audit Trail | 20 s | Architecture (30%) |
| 10 | Outro Scorecard | 15 s | All axes |
| | **Total** | **~4 min 05 s** | |

---

## Screenshot Reference

| Scene | File |
|-------|------|
| 3 | `docs/demo/screenshots/01_chat_portfolio.png` |
| 4 | `docs/demo/screenshots/02_reasoning_trace.png` |
| 6 | `docs/demo/screenshots/03_trap_refusal.png` |
| 7 | `docs/demo/screenshots/04_digital_twin.png` |
| 8 | `docs/demo/screenshots/05_harness.png` |
