# Task wave-9/01 — Automated UI Screenshots (the demo assets judges asked for)

> Read `work/WORKER_PROMPT.md` then build. Produces real PNG screenshots of the Streamlit UI for
> the submission. DEMO-CRITICAL. Depends on W7 (UI, shipped).

## Objective
Script that launches the FinRoot Streamlit UI in Mock mode, drives it through the 4 demo scenarios,
and captures PNG screenshots of each tab (Chat answer card, Reasoning Trace, Digital Twin, Harness)
for the submission deck/README/video thumbnails.

## Writes (ONLY these)
- `scripts/capture_screenshots.py`
- `docs/demo/screenshots/README.md`
- `tests/unit/test_capture_screenshots.py`

## Forbid
`src/interface/**` (import only), any other scripts, `docs/demo/transcript_*.md`.

## Steps
1. `scripts/capture_screenshots.py`:
   - Use Playwright (sync API). Lazy-import; if `playwright` not installed, print clear install
     hint (`pip install playwright && playwright install chromium`) and exit non-zero (FM-11, no
     silent pass).
   - Start Streamlit headless on a free port: `streamlit run src/interface/ui/app.py
     --server.headless true --server.port <PORT>` as a subprocess; wait for `/_stcore/health` == ok.
   - Ensure `FINROOT_LLM_PROVIDER=mock` in the env (offline).
   - For each of the 4 tabs, navigate, type the showcase query where relevant, wait for render,
     and `page.screenshot(path="docs/demo/screenshots/<NN>_<tab>.png", full_page=True)`:
     - `01_chat_portfolio.png` — Chat tab, query "Review my portfolio and flag risks"
     - `02_reasoning_trace.png` — Reasoning Trace tab for that answer
     - `03_trap_refusal.png` — Chat tab, query "Should I put my entire emergency fund into a hot small-cap stock?" (shows the prudence refusal)
     - `04_digital_twin.png` — Digital Twin tab
     - `05_harness.png` — Harness tab (loads results/metrics.json)
   - Always tear down the Streamlit subprocess in a `finally` block.
   - Print the list of PNGs written + their sizes.
2. `docs/demo/screenshots/README.md` — captions for each PNG, what it demonstrates, and which
   judging axis it supports (Reasoning 35% / Architecture 30% / etc.).
3. `tests/unit/test_capture_screenshots.py` (min 4): module imports; the showcase-query list has 5
   entries; the output paths are under `docs/demo/screenshots/`; graceful exit message when
   playwright is absent (monkeypatch the import).

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_capture_screenshots.py -v
# Full run (needs playwright + chromium installed):
PYTHONPATH=src python3 scripts/capture_screenshots.py && ls -la docs/demo/screenshots/*.png
ruff check scripts/capture_screenshots.py
```
If playwright is unavailable in the build env, the unit tests must still pass and the script must
exit with the install hint (capture is then run on the demo machine).

## Report
`work/reports/wave-9-polish/01-ui-screenshots.report.md`
