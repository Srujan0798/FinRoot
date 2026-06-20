# Task wave-12/02 — Final Speaker-Ready Deck

> Read `work/WORKER_PROMPT.md` then build. Pure docs. Turns the slide outline into final content.

## Objective
A speaker-ready 6-slide deck (markdown, one section per slide) with real numbers, tight talking
points, and the visual to show on each slide — ready to drop into Slides/Marp/Pitch.

## Writes (ONLY these)
- `docs/business/slides.md`

## Forbid
`docs/business/presentation_outline.md` (existing — read it, don't edit), `docs/business/executive_summary.md`, README.md, all other files.

## Context (real numbers — FM-12)
- `results/metrics.json` (FRB: finroot mean, lift vs RAG, n_tasks, n domains)
- `docs/business/presentation_outline.md` (the skeleton to expand)
- `docs/architecture/architecture.png` (slide 3 visual)
- `docs/demo/screenshots/*.png` (slide 5 visuals)
- `README.md` (positioning + judging map)

## Steps
`docs/business/slides.md` — 6 slides, each as `## Slide N — <title>` with:
- **On-screen** (3-5 tight bullets, the words that go ON the slide)
- **Say** (2-3 sentences of speaker narration)
- **Show** (the exact asset: which screenshot / the arch png / a metric)
Slides:
1. **The problem** — chatbot ≠ advice (no trace, no risk, no citations, no memory).
2. **Solution / Idea (15%)** — sovereign, reasoning-first, auditable; the Digital Twin moat.
3. **Architecture (30%)** — LangGraph plan-execute, 6 agents, 12 tools, 4-tier memory (show architecture.png).
4. **Reasoning Quality (35%)** — 5-axis critic + prudence verifier + FRB proof (real lift number, show harness screenshot).
5. **Demo** — the live trace + the emergency-fund trap refusal (show trap screenshot).
6. **Why we win** — 4-axis scorecard, sovereignty, audit trail, reproducibility; the close.
Keep it crisp — a judge reads each slide in <20s. Numbers from metrics.json only.

## Acceptance
```bash
test -f docs/business/slides.md && echo "deck present"
grep -cE "^## Slide" docs/business/slides.md   # expect 6
grep -qiE "35%|reasoning" docs/business/slides.md && echo "reasoning slide present"
```

## Report
`work/reports/wave-12-final/02-final-deck.report.md`
