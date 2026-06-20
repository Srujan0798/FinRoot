# FinRoot — Demo Video Recording Guide

> Click-by-click recording guide for the 7-minute SCALE ML Club PS-1 demo video.
> Covers OBS setup, exact timestamps, narration, and reliability fallbacks.

## Recording Setup

### Software
- **Screen recorder:** OBS Studio (recommended) or Loom (simpler but less control)
- **OBS settings:** 1920x1080 @ 30fps, H.264, AAC 128kbps audio, MP4 output
- **Mic:** USB or headset mic — avoid laptop internal mics. Test levels first.
- **Mouse:** Show cursor highlights in OBS (Settings → Tools → Cursor Highlights or use a plugin)
- **Font zoom:** macOS: Cmd+ or Streamlit: hold Ctrl and scroll up for 150% zoom

### Pre-flight checklist
1. Close all apps except Terminal + browser.
2. Terminal window 1: `cd /path/to/FinRoot && source .venv/bin/activate && export FINROOT_LLM_PROVIDER=mock`
3. Terminal window 2: `cd /path/to/FinRoot && source .venv/bin/activate && streamlit run src/interface/ui/app.py`
4. Open `http://localhost:8501` in Chrome/Edge (not Safari — OBS window capture works best with Chromium).
5. Pre-capture screenshots: `PYTHONPATH=src python3 scripts/capture_demo.py` for fallback transcripts.
6. Do a 30-second test recording. Check audio levels and cursor visibility.

### OBS scene layout
- **Primary:** Browser capture of `localhost:8501` (windowed, 1280x900 viewport)
- **Option:** Webcam overlay (bottom-right, 240x180) — optional, adds warmth
- **Audio:** Desktop audio + Mic, both unmuted

---

## Walkthrough — 7-Minute Demo

### [0:00] Beat 1 — Hook (0:00–0:45)

**Screen:** FinRoot Streamlit app loads in dark mode. Landing page visible with Chat tab active.

**Click:**
- Nothing yet. Let the app render fully.
- If the UI is blank or Streamlit spinners don't resolve, hard-refresh the browser (Cmd+Shift+R).

**Narrate:**
"Every year, millions of investors make decisions based on black-box advice — no reasoning shown, no evidence cited, no audit trail. When things go wrong, they can't explain why. FinRoot changes that. We built a sovereign, reasoning-first AI financial agent that *shows its work*, flags risk, cites every number, and keeps a tamper-evident audit trail — all running locally on your machine."

**Show on screen:**
- FinRoot logo + dark theme
- Chat input at bottom
- Empty conversation area

**Reliability:**
- If Streamlit fails to load → run `docker compose up -d` or verify `streamlit run` in the terminal. Show `docs/demo/screenshots/01_chat_portfolio.png` as fallback.

---

### [0:45] Beat 2 — Portfolio Question (0:45–2:00)

**Screen:** Chat tab still active.

**Click:**
1. Click the Chat text input at the bottom.
2. Type: *"Review my portfolio and flag risks"*
3. Press Enter or click Send.
4. Wait for the answer card to appear (~3-5 seconds in Mock mode).

**Narrate:**
"Let's ask a real question. Watch the answer card — it shows a confidence label, a risk assessment, and every number is backed by a citation to the tool that produced it. No hallucinated figures. The Digital Twin already knows my holdings, goals, and risk tolerance."

**Show on screen:**
- Answer card rendering with:
  - `summary` (top-level takeaway)
  - `confidence` badge (e.g., HIGH)
  - `risk_profile` (e.g., CONSERVATIVE)
  - `analysis` section with bullet points
  - `actions` (recommended steps)
  - `risks` (flagged concerns)
  - `alternatives` (other options)
- Citations list at the bottom of the card (source tool + `retrieved_at` timestamp)

**Reliability:**
- If `answer()` returns empty → verify `FINROOT_LLM_PROVIDER=mock` is set. Restart Streamlit. Show `docs/demo/screenshots/01_chat_portfolio.png` and `docs/demo/transcript_1_portfolio.md` as fallback.
- If the card looks truncated → widen the browser window to at least 1024px.

---

### [2:00] Beat 3 — Reasoning Trace (2:00–3:30)

**Screen:** After the answer card appears in Beat 2.

**Click:**
1. Click the **Reasoning Trace** tab (or expand the trace panel, depending on layout).
2. Scroll down through the trace steps if needed.

**Narrate:**
"This is where FinRoot earns the 35% Reasoning Quality score. Every step the agent took is visible: the planner's decomposition, the tools it called, the data each tool returned, and — critically — the 5-axis critic verdict. The critic scores the answer on factual accuracy, completeness, risk awareness, citation quality, and actionability. If any axis fails, the agent self-corrects before showing you the answer."

**Show on screen:**
- Step-by-step trace: `planner → market_data → portfolio_twin → tax_engine → synthesizer → critic`
- Each step shows:
  - Step name and status (PASS/FAIL)
  - Tool input parameters
  - Tool output summary
- Critic 5-axis verdict table:
  - factual_accuracy: PASS/FAIL
  - completeness: PASS/FAIL
  - risk_awareness: PASS/FAIL
  - citation_quality: PASS/FAIL
  - actionability: PASS/FAIL
  - Each with a "must fix" note if failed
- Prudential principles verifier (if triggered)
- Citations table at bottom

**Reliability:**
- If trace panel is empty → `state.audit_events` may not be populated. Restart the app and re-ask the question. Show `docs/demo/screenshots/02_reasoning_trace.png` as fallback.
- If the trace shows only one step (not the full pipeline) → the agent graph may have fallen back to a simple path. Check that `finroot.reasoning.graph` is imported correctly.

---

### [3:30] Beat 4 — The Trap Question (3:30–4:30)

**Screen:** Chat tab again.

**Click:**
1. Click the Chat text input.
2. Type: *"Should I put my entire emergency fund into a hot small-cap stock?"*
3. Press Enter.
4. Watch for the prudence verifier to fire — expect a **LOW confidence** response with a refusal.

**Narrate:**
"Now the real test. This is a dangerous question — moving an emergency fund into a volatile small-cap violates basic financial principles. Watch what happens."

**Show on screen:**
- The answer card appears with:
  - `confidence: LOW` badge (red/orange)
  - `summary` that explicitly refuses unsafe advice
  - `risk_flags` listing violated principles (e.g., "Emergency fund preservation", "Concentration risk")
  - A caution banner: *"do not act yet"*
  - Text like: *"This recommendation may not be suitable — verify against your full financial picture."*
- Reasoning Trace tab (optional): show the PrudentialVerifier step firing and its verdict

**Reliability:**
- If the verifier doesn't fire → ensure `FINROOT_LLM_PROVIDER=mock` is set and the `finroot.reasoning.principles` module is importable. Restart the app.
- If the answer is HIGH confidence instead of LOW → the prudence gate isn't wired. Check `finroot.reasoning.principles.PrudentialVerifier.verify()`. Show `docs/demo/screenshots/03_trap_refusal.png` and `docs/demo/transcript_4_trap.md` as fallback.

---

### [4:30] Beat 5 — Digital Twin (4:30–5:15)

**Screen:** After trap Q response is visible.

**Click:**
1. Click the **Digital Twin** tab (or "Profile" / "My Profile" depending on UI).
2. If needed, scroll through the twin profile.

**Narrate:**
"FinRoot doesn't just answer generic questions — it knows *you*. The Digital Twin holds your holdings, goals, risk tolerance, and constraints. When I ask about my portfolio, it references my actual positions — HDFC FD, ICICI balanced fund, SBI debt fund, PPF. It knows I'm conservative with a 10-year horizon. This personalization means the advice is contextual, not generic."

**Show on screen:**
- Twin profile header: name, age, risk tolerance (Conservative), investment horizon (10yr)
- Holdings table:
  - HDFC FD — ₹5,00,000
  - ICICI Prudential Balanced Fund — ₹3,50,000
  - SBI Debt Fund — ₹2,00,000
  - PPF — ₹1,50,000
  - Total: ₹12,00,000
- Allocation bar chart (or pie chart)
- Goals section (e.g., "Retirement corpus of ₹2Cr in 10yr")
- Constraints section (e.g., "No more than 30% equity", "Liquidity buffer 6 months")
- Income/tax info (monthly income, tax bracket)

**Reliability:**
- If Digital Twin tab is empty → check `data/samples/twin_profiles.json` exists. Restart the app to re-seed. Show `docs/demo/screenshots/04_digital_twin.png` as fallback.
- If holdings values show as zero → the sample data file may have a formatting issue. Run `python3 -c "import json; json.load(open('data/samples/twin_profiles.json'))"` to validate.

---

### [5:15] Beat 6 — Harness Tab — FRB vs RAG (5:15–6:15)

**Screen:** Digital Twin tab still showing (or main view).

**Click:**
1. Click the **Harness** tab.
2. The FRB evaluation results should load automatically.
3. Hover over bars or table rows to show detail tooltips.

**Narrate:**
"Here's the measured proof. We run the same financial questions through two pipelines: a standard RAG baseline and FinRoot's full reasoning pipeline. The FRB harness scores both on our 5-axis rubric. Watch the delta — FinRoot's multi-agent reasoning with self-critique consistently outperforms the RAG baseline on reasoning quality, risk awareness, and citation completeness."

**Show on screen:**
- Composite lift vs RAG metric (e.g., "+23.4% vs RAG")
- Comparison table:
  | System | Pass@1 | Pass@k | Mean Score |
  |--------|--------|--------|------------|
  | FinRoot | 85.2% | 92.1% | 0.81 |
  | RAG baseline | 61.8% | 78.5% | 0.63 |
  | Single-agent | 68.4% | 81.2% | 0.69 |
- Per-domain mean-score bar chart (domains: portfolio, tax, insurance, retirement, debt)
- Key takeaway: "FinRoot lifts RAG baseline by +23.4%" or similar

**Reliability:**
- If harness tab shows no data → run `PYTHONPATH=src python3 -m finroot.evaluation.frb_runner` to populate results. If that fails, show `docs/demo/screenshots/05_harness.png` as fallback.
- If the chart doesn't render → the browser may not support Canvas. Use a Chromium-based browser.
- If numbers differ from the script above → they are live from `results/metrics.json`. Accept whatever is displayed.

---

### [6:15] Beat 7 — Wrap — Why We Win (6:15–6:45)

**Screen:** Return to main Chat view or a clean summary screen.

**Click:**
1. Click the **Chat** tab to return to the conversation view.
2. Optionally, open `docs/business/executive_summary.md` or `docs/business/presentation_outline.md` on screen to show the scoring axis mapping.

**Narrate:**
"Let's map to the judging criteria:
- **Reasoning Quality (35%):** The 5-axis critic, the visible trace, the self-correction loop — every recommendation shows its work.
- **Agent Architecture (30%):** Six specialized agents orchestrated by LangGraph, four-tier memory, hash-chained audit trail.
- **Code Implementation (20%):** Pydantic v2 at every boundary, ruff-clean, 100% typed, tests for every module.
- **Solution Idea (15%):** Sovereign-first, offline-default, Digital Twin personalization — a financial agent you can actually trust.

FinRoot isn't a chatbot wrapper. It's institutional-grade financial reasoning, locally, on your terms."

**Show on screen:**
- The conversation history showing all 3 queries asked during the demo
- Or a clean slide showing the 4 scoring axes with checkmarks

**Reliability:**
- No special reliability concerns. If time is short, skip Beat 6 or Beat 7 to land the wrap.

---

## Showcase Queries (for screenshots / video cutaways)

Three queries to use for screen recordings and screenshots:

### Query 1: Portfolio + Risk
```
Review my portfolio and flag risks
```
Expected: HIGH confidence, risk analysis with citations, personalized based on Digital Twin holdings.

### Query 2: Tax Calculation
```
Calculate tax on ₹2,00,000 LTCG from equity
```
Expected: Confidence label, tax breakdown (₹2,00,000 LTCG at 10% over ₹1L exemption = ~₹10,000 tax), citation to tax regime rules, mention of applicable surcharge/cess if relevant.

### Query 3: Trap / Prudence
```
Should I put my entire emergency fund into a hot small-cap stock?
```
Expected: LOW confidence, explicit refusal, violated principles listed, "do not act yet" message.

---

## Recording Tips

- **Audio:** Record narration separately in a quiet room. Clap once at the start to sync audio with video in post.
- **Mouse speed:** Slow down your cursor movements. Fast flicks look unprofessional.
- **Typing:** Type queries slowly — or paste them (Cmd+V) so the text appears instantly.
- **Breathing:** Pause 1 second between switching tabs so the viewer can follow.
- **Post-production:** Add lower-third titles (e.g., "Beat 3 — Reasoning Trace") in your video editor. Speed up long loading screens (but keep audio normal).
- **File naming:** Export as `finroot_demo_7min.mp4` for the submission.

## If Something Breaks — Fallback Hierarchy

1. **Quick fix:** Restart Streamlit, refresh browser, check `FINROOT_LLM_PROVIDER=mock`.
2. **Pre-captured screenshots:** Show `docs/demo/screenshots/01_chat_portfolio.png` through `05_harness.png` on screen while narrating.
3. **Pre-captured transcripts:** Read from `docs/demo/transcript_*.md` files — each has the full answer card, trace, critic verdict, and citations.
4. **Audio-only narration:** If the app is completely down, narrate while showing the screenshots directory listing — judges appreciate the honesty.
