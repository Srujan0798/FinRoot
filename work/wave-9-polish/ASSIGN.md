# Wave-9 Polish — Assignment Sheet (copy-paste to your agents)

> Optional "ultra-polish" wave. The 8 core waves are SHIPPED & verified (785 tests, +662% FRB lift,
> demo works offline). These 3 tasks produce the **visual demo assets** the organizers asked for
> (screenshots, demo cast, repo/release). All write-sets are **disjoint** — run all 3 in parallel.

## Tasks
| # | Task | Writes | Model suggestion |
|---|------|--------|------------------|
| 01 | UI screenshots (Playwright → PNGs) | `scripts/capture_screenshots.py`, `docs/demo/screenshots/README.md`, `tests/unit/test_capture_screenshots.py` | `opencode/deepseek-v4-flash-free` |
| 02 | CLI demo cast (asciinema → SVG/GIF) | `scripts/record_cli_demo.sh`, `docs/demo/cli_demo.md` | `opencode/nemotron-3-ultra-free` |
| 03 | GitHub publish helper + release notes | `scripts/publish_github.sh`, `docs/RELEASE_NOTES.md` | `xiaomi-token-plan-sgp/mimo-v2.5-pro` |

## Dispatch (parallel — paste into 3 terminals or run the block)
```bash
cd /Users/srujansai/Desktop/FinRoot

bash orchestrator/scripts/dispatch_worker.sh opencode "opencode/deepseek-v4-flash-free" \
  wave-9-polish work/wave-9-polish/01-ui-screenshots.md &

bash orchestrator/scripts/dispatch_worker.sh opencode "opencode/nemotron-3-ultra-free" \
  wave-9-polish work/wave-9-polish/02-cli-demo-cast.md &

bash orchestrator/scripts/dispatch_worker.sh opencode "xiaomi-token-plan-sgp/mimo-v2.5-pro" \
  wave-9-polish work/wave-9-polish/03-github-publish.md &

wait
```

## After they finish — orchestrator acceptance (run yourself, FM-09)
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_capture_screenshots.py -v
bash -n scripts/publish_github.sh && echo "publish script syntax OK"
bash scripts/publish_github.sh finroot-demo        # DRY RUN — must push NOTHING
# On the demo machine (needs playwright + chromium):
#   pip install playwright && playwright install chromium
#   PYTHONPATH=src python3 scripts/capture_screenshots.py
#   bash scripts/record_cli_demo.sh
```

## Notes
- Screenshots/cast need a desktop with `playwright`/`asciinema` — if the agent's env lacks them, the
  scripts are written + unit-tested now, and YOU run the capture on your machine for the real PNGs.
- Task 03 is **dry-run by default** (blast radius r3). It pushes only when you add `--confirm`.
- Nothing here changes shipped code — these are additive demo assets only (FM-08 scope-safe).
