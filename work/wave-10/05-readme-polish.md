# Task wave-10/05 — README Screenshots + Polish

> Read `work/WORKER_PROMPT.md` then build. First impression for judges.

## Objective
Polish the README to include the captured screenshots, improve the architecture section, and add
a "Quick Demo" section that works in 30 seconds.

## Writes (ONLY these)
- `README.md` (update existing)
- `docs/demo/screenshots/README.md` (update existing with captions)

## Forbid
All other files.

## Steps
1. Read existing `README.md` and `docs/demo/screenshots/`.
2. Update README.md:
   - Add screenshots to the "Demo" section: `![Portfolio](docs/demo/screenshots/01_chat_portfolio.png)` etc.
   - Add a "Quick Demo" section: 3 commands to run the demo in 30 seconds
   - Add a "Screenshots" section with all 5 PNGs and captions
   - Add a "FRB Results" section with the per-domain table
   - Ensure all numbers come from results/metrics.json (FM-12)
   - Add the architecture diagram image if it exists
3. Update `docs/demo/screenshots/README.md`:
   - Add captions for each screenshot
   - Add which judging axis each supports
   - Add the query that produced each screenshot

## Acceptance
```bash
test -f README.md && echo "README present"
grep -q "screenshots" README.md && echo "screenshots referenced"
grep -q "Quick Demo" README.md && echo "quick demo section present"
```

## Report
`work/reports/wave-10/05-readme-polish.report.md`
