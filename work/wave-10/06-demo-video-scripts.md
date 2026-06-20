# Task wave-10/06 — Demo Video Script + Recording Guide

> Read `work/WORKER_PROMPT.md` then build. The "wow factor" for judges.

## Objective
Create a detailed, click-by-click recording guide for the 7-minute demo video. Include exact
timestamps, what to click, what to say, and what to show on screen. Also create a shorter
2-minute "highlight reel" script for the submission page.

## Writes (ONLY these)
- `docs/business/demo_recording_guide.md`
- `docs/business/highlight_reel_script.md`

## Forbid
All other files.

## Steps
1. Read existing `docs/business/7_minute_demo_script.md` and `docs/demo/screenshots/`.
2. `docs/business/demo_recording_guide.md`:
   - Detailed recording instructions (OBS/Loom/screencast setup)
   - Exact timestamps for each beat (0:00-7:00)
   - What to click in Streamlit UI for each beat
   - What to say (narration script)
   - What to show on screen (which tab, which query)
   - Include the 3 showcase queries:
     - "Review my portfolio and flag risks"
     - "Calculate tax on ₹2,00,000 LTCG from equity"
     - "Should I put my entire emergency fund into a hot small-cap stock?"
   - Include "if X breaks, do Y" reliability notes
3. `docs/business/highlight_reel_script.md`:
   - 2-minute version for the submission page
   - Key beats: problem → portfolio demo → trap refusal → FRB results → architecture
   - Each beat: 15-20 seconds, what to show, what to say
   - Include the "money shot" (trap refusal with prudence gate)

## Acceptance
```bash
test -f docs/business/demo_recording_guide.md && echo "recording guide present"
test -f docs/business/highlight_reel_script.md && echo "highlight reel present"
grep -q "0:00" docs/business/demo_recording_guide.md && echo "timestamps present"
```

## Report
`work/reports/wave-10/06-demo-video-scripts.report.md`
