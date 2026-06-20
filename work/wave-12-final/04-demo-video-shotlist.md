# Task wave-12/04 — Demo Video Shot List + Narration

> Read `work/WORKER_PROMPT.md` then build. Pure docs. The precise scene-by-scene recording guide.

## Objective
A scene-by-scene shot list so the presenter records a tight, professional demo video fast — every
scene has: what's on screen, exact click/keystroke, the words to say, and the duration.

## Writes (ONLY these)
- `docs/business/demo_video_shotlist.md`

## Forbid
`docs/business/7_minute_demo_script.md` (existing — read it, complement it, don't edit),
`docs/business/slides.md`, README.md, all other files.

## Context
- `docs/business/7_minute_demo_script.md` (the timed script — make the shot list operational)
- `docs/demo/screenshots/*.png` (what each scene should look like)
- The 3 showcase queries; the UI tabs (Chat / Reasoning Trace / Digital Twin / Harness)

## Steps
`docs/business/demo_video_shotlist.md` — a table/sequence of ~10-12 scenes, each row:
`# | duration | on-screen | action (click/type) | say (verbatim narration) | fallback if it breaks`
Cover this arc (target 3-5 min, tight):
1. Cold open — the one-line pitch + the problem (10s).
2. Launch (show it runs offline, Mock badge) (15s).
3. Portfolio query → answer card (confidence, risk, citations) (30s).
4. Reasoning Trace tab → plan → tools → 5-axis critic verdict (the 35% moment) (40s).
5. Tax query with ₹ amount → the cited ₹10,400 result (25s).
6. The emergency-fund trap → prudence refusal, confidence downgraded to LOW (the wow moment) (40s).
7. Digital Twin tab → personalization (20s).
8. Harness tab → the FRB lift vs RAG (the proof) (30s).
9. Audit trail / sovereignty close (20s).
10. Outro — 4-axis scorecard + repo link (15s).
Include: pre-record checklist (terminal font size, window size, `rm -f data/digital_twin.db` for a
clean run, Mock on), and a "record in 2 takes" tip. Reference the real screenshots by filename.

## Acceptance
```bash
test -f docs/business/demo_video_shotlist.md && echo "shotlist present"
grep -ciE "say|narrat|scene|duration" docs/business/demo_video_shotlist.md
grep -qiE "emergency fund|trap" docs/business/demo_video_shotlist.md && echo "trap scene present"
```

## Report
`work/reports/wave-12-final/04-demo-video-shotlist.report.md`
