# Report wave-12-final/04 — Demo Video Shot List + Narration

## Result
DONE

## What I built
- `docs/business/demo_video_shotlist.md` — scene-by-scene shot list with 10 scenes (~4 min 05 s total), pre-record checklist, verbatim narration, on-screen descriptions, click/keystroke actions, fallback instructions, and screenshot references.

## Acceptance evidence (real output, this session)
```
$ test -f docs/business/demo_video_shotlist.md && echo "shotlist present"
shotlist present

$ grep -ciE "say|narrat|scene|duration" docs/business/demo_video_shotlist.md
25

$ grep -qiE "emergency fund|trap" docs/business/demo_video_shotlist.md && echo "trap scene present"
trap scene present
```

## Tests
- N/A (pure documentation task — no code to test). Document passes all 3 acceptance grep checks.

## Decisions / deviations
- Structured as a markdown table per scene (not a flat list) for quick scanning during recording.
- Added a Pre-Record Checklist section (terminal font, window size, clean DB, Mock mode, 2-take tip) per task requirements.
- Total runtime ~4:05, within the 3–5 min target.
- Referenced all 5 real screenshots by filename from `docs/demo/screenshots/`.

## Surprises / gotchas
- N — no surprises encountered.

## Follow-ups (for orchestrator triage — do NOT build now)
- Could add a "teleprompter mode" copy-paste block for each scene's narration (single text blob per scene).

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; no financial data needed (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] N/A — pure docs, no code to lint or test
- [x] No secrets committed (FM-07)
