# Task wave-9/02 — CLI Demo Cast (terminal GIF/SVG for the README + video)

> Read `work/WORKER_PROMPT.md` then build. Produces an animated terminal recording of the CLI
> running the 3 showcase queries. Depends on W7 (CLI, shipped).

## Writes (ONLY these)
- `scripts/record_cli_demo.sh`
- `docs/demo/cli_demo.md`

## Forbid
`src/**` (call the installed CLI only), other scripts, `docs/demo/screenshots/**`.

## Steps
1. `scripts/record_cli_demo.sh` (bash, `set -euo pipefail`):
   - Detect `asciinema` (preferred) → record a cast of running, in sequence (Mock mode):
     - `python -m interface.cli --mock "Review my portfolio and flag risks"`
     - `python -m interface.cli --mock "Calculate tax on ₹2,00,000 LTCG from equity"`
     - `python -m interface.cli --mock "Should I put my entire emergency fund into a hot small-cap stock?"`
   - Output `docs/demo/cli_demo.cast`. If `agg` or `svg-term` is available, also render
     `docs/demo/cli_demo.svg` / `.gif`.
   - If `asciinema` is NOT installed: fall back to writing a plain captured transcript
     `docs/demo/cli_demo.txt` (run the 3 commands, tee their output) and print the install hint for
     asciinema — do NOT fail silently (FM-11).
   - Always set `PYTHONPATH=src` and `FINROOT_LLM_PROVIDER=mock`.
2. `docs/demo/cli_demo.md` — embeds/links the cast (asciinema badge or the SVG), with a 2-line
   caption per query explaining what to notice (the reasoning trace, the tax citation, the prudence
   refusal).

## Acceptance
```bash
bash scripts/record_cli_demo.sh          # produces docs/demo/cli_demo.{cast,svg} or .txt fallback
ls -la docs/demo/cli_demo.*
test -f docs/demo/cli_demo.md && echo "cli demo doc present"
```
Note in the report which tool path was taken (asciinema vs txt fallback) — FM-09.

## Report
`work/reports/wave-9-polish/02-cli-demo-cast.report.md`
