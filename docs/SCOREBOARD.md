# FinRoot SCOREBOARD

> Living truth table. Cells move RED → YELLOW → GREEN **only with evidence path**.  
> As of: 2026-07-25 · post Phase-1 fixes · Baseline: `work/reports/P0-baseline.md`  
> **Blended honest score: ~83%** (not 100%). Evidence: `work/reports/wave-ultra/PHASE1_GATE.md`

Legend: **RED** broken/unproven · **YELLOW** partial · **GREEN** evidenced this freeze window

---

## A. PS-1 Rubric

| Criterion | W | Status | % | Evidence / gap |
|---|---:|---|---:|---|
| Solution Idea | 15% | YELLOW | 84 | Novelty real; disclaimers added |
| Agent Architecture | 30% | YELLOW | 86 | Intent scoring + intent-wins domain |
| Reasoning Quality | 35% | YELLOW | 84 | GP green; FRB pass@1 **0.506** mean **0.8677** lift **+155%** @22acede |
| Code Implementation | 20% | YELLOW | 82 | Golden + metrics/zip green; CI hardened; some suite edges may remain |
| **BLENDED** | 100% | YELLOW | **~86** | Target freeze ≥ **95** for top 0.1% claim |

---

## B. Sacred Golden Paths

| ID | Path | Status | Evidence |
|---|---|---|---|
| GP-1 | Portfolio rebalance CLI/UI | **GREEN** | answer() + golden test |
| GP-2 | LTCG tax numeric India | **GREEN** | tax compute ₹0 on 1L; not news; golden test |
| GP-3 | Emergency fund → small-cap trap | **YELLOW** | RISK routing; deepen refuse copy |
| GP-4 | Loan to buy stocks | **GREEN** | Intent RISK; prudence path |
| GP-5 | VaR / drawdown | **GREEN** | Intent RISK; prudence compliant (no 95% FP) |
| Smoke | `scripts/smoke_test.py` | **GREEN** | FOUNDATION OK |
| Full pytest | `pytest tests/` | **YELLOW** | metrics/zip green after evals; re-running fast suite |
| Docker | `docker compose up` | **YELLOW** | File exists; not re-browsered this session |
| Streamlit 4 tabs | Chat/Trace/Twin/Harness | **YELLOW** | disclaimer+badge landed; browser proof pending |
| FRB metrics | results/metrics.json | **GREEN** | as_of_sha=22acede pass@1=0.506 mean=0.8677 lift=154.98% |
| Audit chain | hash-chained JSONL | **GREEN** | smoke + unit surface |
| No secrets | repo + zip | **GREEN** | zip rebuilt; secret scan hard-fail in CI |
| No trade execution | r5 | **GREEN** | security workflow guard |
| Docs honesty | HANDOFF/README | **YELLOW** | HANDOFF reset; kill other overclaims |
| NFA disclaimer UI | visible | **RED** | missing on main shell |
| Mock badge | never sold as live LLM | **YELLOW** | toggle default true; label strengthen |

---

## C. Functional requirements (PRD C1–C10)

| FR | Status | Note |
|---|---|---|
| C1 Portfolio reasoning | YELLOW/GREEN | Works mock; polish concentration language |
| C2 Risk analysis | YELLOW | Tools exist; routing GP-5 broken |
| C3 Market & news | YELLOW | Tools; intent steals other domains |
| C4 Tax India | **GREEN** | Parse + engine + tax summary E2E mock |
| C5 Cashflow | YELLOW | Domain templates; less E2E proof |
| C6 Credit/debt | YELLOW | Loan+invest → RISK (correct for trap) |
| C7 Scenario simulation | GREEN/YELLOW | Monte Carlo visible in portfolio run |
| C8 Explainable DS | YELLOW | Trace good; summary can mismatch domain |
| C9 Digital Twin | GREEN | Demo twin seeds |
| C10 Audit export | GREEN | trail + events on state |

---

## D. Phase gate tracker

| Phase | Name | Gate | Status |
|------:|---|---|---|
| 0 | Truth reset | SCOREBOARD + audit + baseline exist; no COMPLETE lie | **GREEN** |
| 1 | Reasoning fortress (P0) | GP-1..5 green tests | **GREEN** (core) |
| 2 | Golden path stranger | Judge quickstart 10-min dry run | RED |
| 3 | Depth / FRB | pass@1 ≥ 0.55 or honest label; domain means stable | YELLOW |
| 4 | Completeness | PRD C1–C10 yellow→green | YELLOW |
| 5 | Brownies | PDF/goal/FX/counterfactual demos | YELLOW |
| 6 | Architecture polish | fail-loud, INR, health honesty | YELLOW |
| 7 | UI domination | disclaimer, mock badge, density | **YELLOW** (disclaimer+badge done) |
| 8 | Automated proof | CI hard gates + playwright/API smoke | RED |
| 9 | Freeze | checklist all green + evidence | RED |

---

## E. Definition of 100% (freeze — do not check lightly)

- [ ] All SCOREBOARD A rows GREEN with pasted commands  
- [ ] GP-1..GP-5 automated tests green  
- [ ] Security: no secrets; no trade exec; injection tests pass; API labeled single-user  
- [ ] Mock never presented as live cloud intelligence  
- [ ] FRB regenerated this freeze SHA; numbers match docs  
- [ ] `make ci` green without `|| true` on critical steps  
- [ ] Browser or Playwright proof of UI golden path  
- [ ] HANDOFF rewritten honest  
- [ ] You would bet a hostile judge cannot kick FinRoot in 10 minutes  

**If any box open → report REAL % · never invent 100%.**
