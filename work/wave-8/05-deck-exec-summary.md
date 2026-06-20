# Task wave-8/05 — 6-Slide Deck Outline + Executive Summary

> Read `work/WORKER_PROMPT.md` then build. Depends on all waves. The pitch.

## Objective
A crisp 6-slide deck outline and a one-page executive summary that sell FinRoot to judges on all
four scoring axes.

## Writes (ONLY these)
- `docs/business/presentation_outline.md`
- `docs/business/executive_summary.md`

## Forbid
All other files. Read `results/metrics.json` (if present) for numbers; read `CLAUDE.md` for positioning.

## Contract
Read `.specify/specs/wave-8/contracts/submission.contract.md` § Deck + exec summary.

## Steps
1. `docs/business/presentation_outline.md` — 6 slides, each with: title, 3-5 bullet talking points, the visual/asset to show, and the "so what" line. Slides:
   1. **Problem** — individual investors vs institutional-grade reasoning.
   2. **Solution / Idea (15%)** — FinRoot: sovereign, reasoning-first, auditable; the Digital Twin moat.
   3. **Agent Architecture (30%)** — LangGraph plan-execute, 6 agents, 12 tools, 4-tier memory; show the diagram.
   4. **Reasoning Quality (35%)** — 5-axis self-critic + principles verifier + FRB results (lift vs RAG from metrics.json).
   5. **Demo** — the live reasoning trace + trap refusal + harness.
   6. **Why we win** — the 4-axis scorecard, sovereignty, audit trail, reproducibility.
2. `docs/business/executive_summary.md` — one page: what it is, why it matters (the problem + the gap), the measured edge (FRB lift — from metrics.json, cite as_of_sha; if absent, note "regenerate via make evals"), the moat (Digital Twin + sovereign + audit), and the ask.
- Numbers come from `results/metrics.json` (FM-12). If absent, reference how to regenerate — never fabricate.

## Acceptance
```bash
test -f docs/business/presentation_outline.md && test -f docs/business/executive_summary.md && echo "files present"
grep -qiE "35%|reasoning" docs/business/presentation_outline.md && echo "reasoning slide present"
wc -l docs/business/executive_summary.md
```

## Report
`work/reports/wave-8/05-deck-exec-summary.report.md`
