# Task wave-12/03 — README Hero Demo Cast

> Read `work/WORKER_PROMPT.md` then build. Adds an "alive" terminal demo near the top of the README.

## Objective
A short, self-contained terminal cast of the CLI running the 3 showcase queries, plus a README hero
embed so the first thing a judge sees is the agent reasoning + refusing bad advice.

## Writes (ONLY these)
- `scripts/record_hero_cast.sh`
- `docs/demo/hero.md`
- `README.md`   (ONLY add the hero embed block near the top — do not restructure the rest)

## Forbid
docs/business/**, docs/SUBMISSION_MESSAGE.md, docs/JUDGE_QUICKSTART.md, scripts/capture_demo.py,
scripts/record_cli_demo.sh (different file), all other files.

## Steps
1. `scripts/record_hero_cast.sh` (bash, `set -euo pipefail`):
   - Prefer `asciinema rec` of the 3 CLI commands (portfolio / ₹ tax / emergency-fund trap) in
     Mock mode (PYTHONPATH=src FINROOT_LLM_PROVIDER=mock). Output `docs/demo/hero.cast`.
   - If `agg`/`svg-term-cli` present, render `docs/demo/hero.svg` / `hero.gif`.
   - Fallback (no asciinema): write `docs/demo/hero.txt` from the live command output. Fail loud
     with the install hint if neither path works (FM-11) — never silent.
2. `docs/demo/hero.md` — embeds the cast (asciinema badge / SVG) + a 1-line caption per query.
3. `README.md` — insert a single hero block right under the badges / one-line pitch:
   - A link/embed to the cast (use the SVG if present, else link `docs/demo/hero.md`), and one of
     the existing screenshots (`docs/demo/screenshots/03_trap_refusal.png`) as the hero image.
   - Make MINIMAL changes — add one block, touch nothing else. Verify README still renders (no
     broken markdown).

## Acceptance
```bash
bash -n scripts/record_hero_cast.sh && echo "script syntax OK"
bash scripts/record_hero_cast.sh && ls -la docs/demo/hero.*    # produces cast/svg or txt fallback
test -f docs/demo/hero.md && echo "hero doc present"
grep -q "docs/demo/" README.md && echo "README hero embed present"
python3 -c "open('README.md').read()" && echo "README readable"
```

## Report
`work/reports/wave-12-final/03-readme-hero-cast.report.md`
