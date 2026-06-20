# Report wave-9-polish/02 — CLI Demo Cast

## Result
DONE

## What I built
- `scripts/record_cli_demo.sh` — bash recording script (asciinema preferred, txt fallback)
- `docs/demo/cli_demo.md` — markdown documentation embedding the demo with captions

## Acceptance evidence (real output, this session)
```
$ bash scripts/record_cli_demo.sh
asciinema NOT found — falling back to plain text transcript.
Install asciinema for animated casts: pip install asciinema

Transcript written to: docs/demo/cli_demo.txt

$ ls -la docs/demo/cli_demo.*
-rw-r--r--@ 1 srujansai  staff   2831 Jun 20 15:23 /Users/srujansai/Desktop/FinRoot/docs/demo/cli_demo.md
-rw-r--r--@ 1 srujansai  staff  12906 Jun 20 15:23 /Users/srujansai/Desktop/FinRoot/docs/demo/cli_demo.txt

$ test -f docs/demo/cli_demo.md && echo "cli demo doc present"
cli demo doc present
```

**Tool path taken**: Text fallback (asciinema/agg/svg-term not installed). The script detects missing tools and falls back to capturing a plain transcript, printing the install hint — satisfying FM-11 (no silent failures).

## Tests
- All 133 existing tests pass (`python3 -m pytest tests/ -x -q` → 100% pass)
- No new tests added (bash script + markdown; no Python code to test)

## Decisions / deviations
- Used `grep -v` to filter deprecation warnings from the transcript for readability
- The `--command` string for asciinema uses a heredoc-style approach; if asciinema is later installed, it will record a proper `.cast` file
- Markdown doc links to the text transcript with line-range anchors; when asciinema is available, the doc can be updated to embed the SVG badge

## Surprises / gotchas
- Python 3.14 deprecation warnings (Pydantic v1, LangGraph) appear in CLI output; filtered in transcript
- Added to `docs/waves/wave-9-polish-gotchas.md`? **N** (no new gotchas beyond known deprecation warnings)

## Follow-ups (for orchestrator triage — do NOT build now)
- Install asciinema in CI to generate animated casts for README
- Consider adding a `make demo` target that installs asciinema and regenerates assets
- The transcript filtering could be improved to preserve ANSI colors for SVG rendering

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks (script uses `set -euo pipefail`, explicit fallback with message)
- [x] ruff clean, tests green (no Python files to lint; all 133 tests pass)
- [x] No secrets committed (FM-07)