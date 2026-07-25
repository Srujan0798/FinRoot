# HANDOFF — Current State

> Replaced 2026-07-25 (ULTRA WIN execution). Read this first.

## Snapshot
- **Project:** FinRoot — SCALE ML Club PS-1 financial agent
- **Honest blended score (PS-1 weighted):** **~86%** — **not 100%, not freeze-ready**
- **FRB (regenerated):** mean **0.8677** · pass@1 **0.5060** · lift **+154.98%** · `as_of_sha=bc8cc5b`
- **Plan:** `work/ETERNAL_FINAL_PLAN.md`
- **Scoreboard:** `docs/SCOREBOARD.md`
- **Phase 1 evidence:** `work/reports/wave-ultra/PHASE1_GATE.md`
- **30m improvement loop:** durable scheduler active

## Landed this session
| Area | Fix |
|---|---|
| Intent | Priority scoring; loan+stocks→RISK; VaR+portfolio→RISK; LTCG denylist |
| Tax | Parse `1L`/₹/lakh; engine runs; summary shows computed tax |
| Domain | Intent wins (tax no longer becomes news) |
| Prudence | VaR 95% confidence ≠ concentration FP |
| Mock LLM | Domain-biased canned pools |
| Market | INR for India demo symbols |
| UI | NFA disclaimer + mock badge |
| Golden | `tests/golden/test_golden_paths_ps1.py` green |
| FRB | `make evals` k=1 → metrics @ HEAD bc8cc5b |
| Zip | `finroot-submission.zip` rebuilt; metrics/zip tests green |
| CI | Hard-fail secrets; install no longer `\|\| true`; fast test path |

## Sacred acceptance (keep green)
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_intent.py tests/golden/test_golden_paths_ps1.py tests/unit/test_metrics_freshness.py tests/unit/test_zip_consistency.py -q
PYTHONPATH=src python3 scripts/smoke_test.py   # FOUNDATION OK
```

## Still open → top 0.1% / freeze
1. Full/fast pytest residual (if any after regen)
2. Browser / Playwright proof of Streamlit golden path
3. pass@1 stretch ≥0.55 (optional)
4. Phase 9 freeze checklist in SCOREBOARD §E

## Score path
| Stage | % |
|---|---:|
| Audit baseline | 68 |
| Phase 1 GP fixes | ~83 |
| **Now (+evals+zip+CI)** | **~86** |
| Freeze target | ≥95 |

**Never claim submission-ready without Phase 9 checklist + evidence.**
