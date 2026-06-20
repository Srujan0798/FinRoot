# Report wave-9/01 — Automated UI Screenshots

## Result

DONE

## What I built

- `scripts/capture_screenshots.py` — Playwright-based script that launches Streamlit headless in Mock mode, drives all 4 tabs, submits the 2 showcase queries, and captures 5 PNG screenshots.
- `docs/demo/screenshots/README.md` — Captions for each screenshot, mapping to judging axes.
- `tests/unit/test_capture_screenshots.py` — 6 tests (module imports, list length = 5, paths under `docs/demo/screenshots/`, graceful playwright-absent exit, expected filenames).
- `docs/waves/wave-9-polish-gotchas.md` — 3 gotchas encountered during implementation.

## Acceptance evidence (real output, this session)

```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_capture_screenshots.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
collected 6 items

tests/unit/test_capture_screenshots.py ......                            [100%]

============================== 6 passed in 0.14s ===============================

$ PYTHONPATH=src python3 scripts/capture_screenshots.py && ls -la docs/demo/screenshots/*.png

Done. 5 screenshot(s) written:
  docs/demo/screenshots/01_chat_portfolio.png  (111,140 bytes)
  docs/demo/screenshots/02_reasoning_trace.png  (101,062 bytes)
  docs/demo/screenshots/03_trap_refusal.png  (109,670 bytes)
  docs/demo/screenshots/04_digital_twin.png  (53,605 bytes)
  docs/demo/screenshots/05_harness.png  (88,108 bytes)
-rw-r--r--@ 1 srujansai  staff  111140 Jun 20 15:25 docs/demo/screenshots/01_chat_portfolio.png
-rw-r--r--@ 1 srujansai  staff  101062 Jun 20 15:25 docs/demo/screenshots/02_reasoning_trace.png
-rw-r--r--@ 1 srujansai  staff  109670 Jun 20 15:25 docs/demo/screenshots/03_trap_refusal.png
-rw-r--r--@ 1 srujansai  staff   53605 Jun 20 15:25 docs/demo/screenshots/04_digital_twin.png
-rw-r--r--@ 1 srujansai  staff   88108 Jun 20 15:25 docs/demo/screenshots/05_harness.png

$ ruff check scripts/capture_screenshots.py
All checks passed!
```

## Tests

- 6 tests in `tests/unit/test_capture_screenshots.py` — all pass.
- Full capture script runs successfully end-to-end (5 PNGs produced).

## Decisions / deviations

- Used `page.get_by_role("tab").filter(has_text=...)` for tab navigation instead of index-based approach (more robust to Streamlit CSS changes).
- Chat input selected as `[data-testid="stChatInput"] textarea` after discovering the outer `div` does not accept `.fill()`.
- Added `docs/waves/wave-9-polish-gotchas.md` with 3 entries discovered during implementation.

## Surprises / gotchas

- Added to `docs/waves/wave-9-polish-gotchas.md`. Key: `stChatInput` is a `<div>`, not an input element — must use child `textarea` selector.

## Follow-ups (for orchestrator triage — do NOT build now)

- Screenshots could be validated programmatically (min dimensions, non-blank via pixel variance).
- Could add a `--port` flag for CI environments where port binding is restricted.

## Self-check

- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
