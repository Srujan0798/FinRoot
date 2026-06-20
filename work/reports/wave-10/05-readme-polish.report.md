# Report wave-10/05 — README Screenshots + Polish

## Result
DONE

## What I built
- `README.md` — added Screenshots section (5 PNGs with captions), Quick Demo section (3 commands), updated FRB Results table with actual `results/metrics.json` numbers (sha 2b4f879, n=52, k=1)
- `docs/demo/screenshots/README.md` — added per-screenshot captions, judging axis mapping, and queries that produced each screenshot

## Acceptance evidence (real output, this session)
```
$ test -f README.md && echo "README present" && grep -q "screenshots" README.md && echo "screenshots referenced" && grep -q "Quick Demo" README.md && echo "quick demo section present"
README present
screenshots referenced
quick demo section present
```

## Tests
- No code changes — documentation-only task. No tests applicable.

## Decisions / deviations
- Updated FRB Results table to reflect current `results/metrics.json` (sha 2b4f879, 52 tasks, 11 domains). Old README had stale numbers from an earlier eval run (sha 5a4d105, 32 tasks).
- Added per-domain score table for FinRoot (all 11 domains from metrics.json).
- Screenshots README uses expanded format with separate subsections per screenshot for clarity.

## Surprises / gotchas
- The existing `results/metrics.json` had significantly different numbers from what the old README cited (52 tasks vs 32, different sha). Updated the README to match the current truth.

## Follow-ups (for orchestrator triage — do NOT build now)
- None.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (N/A — doc-only)
- [x] No secrets committed (FM-07)
