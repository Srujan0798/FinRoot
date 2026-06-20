# Task wave-8/04 — 7-Minute Demo Script + Demo Capture Tool

> Read `work/WORKER_PROMPT.md` then build. Depends on W7 (UI). The narration for the video.

## Objective
A timed, click-by-click 7-minute demo script judges (or the presenter) follow, plus a script that
captures real `answer()` outputs to markdown transcripts for screenshots/video.

## Writes (ONLY these)
- `docs/business/7_minute_demo_script.md`
- `scripts/capture_demo.py`

## Forbid
All other files. `src/**` import only.

## Contract
Read `.specify/specs/wave-8/contracts/submission.contract.md` § Demo script + DEMO ASSETS.

## Steps
1. `docs/business/7_minute_demo_script.md` — timed beats (0:00–7:00). For each beat: **[mm:ss] — what to click — what to say**. Cover:
   - 0:00 Hook: the problem + the one-liner.
   - 0:45 Ask a portfolio question in Chat → answer card appears (confidence + risk + citations).
   - 2:00 Open Reasoning Trace → walk the plan → tools → critic 5-axis verdict (the 35% moment).
   - 3:30 Trap question ("put my emergency fund in this small-cap") → principles verifier refuses / caveats — show the agent says "do not act yet".
   - 4:30 Digital Twin tab → personalization story.
   - 5:15 Harness tab → run FRB → show the lift vs RAG (the measured proof).
   - 6:15 Audit trail → tamper-evident hash chain → sovereignty/offline close.
   - 6:45 Wrap: why we win on all 4 axes.
   - Include a "if X breaks, do Y" reliability note per beat.
2. `scripts/capture_demo.py`:
   - Runs `interface.core.answer()` on 4 showcase queries in Mock (one per: portfolio, tax with a number, news_impact, a trap question).
   - For each: write `docs/demo/transcript_<n>_<slug>.md` containing the query, the answer card, the reasoning trace (build_trace), the critic verdict, and citations — formatted for screenshots.
   - Print a summary of files written. Fail loud if `answer()` import fails (FM-11).

## Acceptance
```bash
PYTHONPATH=src python3 scripts/capture_demo.py
ls docs/demo/transcript_*.md
test -f docs/business/7_minute_demo_script.md && grep -qE "[0-9]:[0-9][0-9]" docs/business/7_minute_demo_script.md && echo "timed script present"
```

## Report
`work/reports/wave-8/04-demo-script.report.md`
