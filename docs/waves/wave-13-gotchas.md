# Wave 13 — Gotchas

## 02 — Hosted Demo Link

1. **No `.specify/specs/wave-13/contracts/` directory.**
   The task references `.specify/specs/wave-13/contracts/` but the directory does not exist.
   This is consistent with wave-12-final (same observation). Not a blocker.

2. **`requirements.txt` triggers ruff `invalid-syntax` errors.**
   Ruff ~0.5 attempts to parse `requirements.txt` as Python when the file is passed directly.
   Comma-separated version specifiers like `langchain>=0.3,<0.4` are valid PEP 508 pip syntax
   but not valid Python. Workaround: only run `ruff check` on `.py` files, or add
   `requirements.txt` to `[tool.ruff].exclude`.

3. **`streamlit_app.py` emits warnings on import outside Streamlit runtime.**
   `st.set_page_config()` called at module level produces "missing ScriptRunContext" warnings
   when the file is imported (not run via `streamlit run`). These are harmless — Streamlit
   >=1.36 does not raise. The acceptance command confirms import succeeds.

4. **`langgraph` has no `__version__` attribute.**
   Unlike most packages, `langgraph` (v0.2.76) does not expose `__version__`.
   Version check via `pip show langgraph` works instead.

## 01 — Test-Infra Honesty

1. **`pytest.ini` takes precedence over `pyproject.toml`'s `[tool.pytest.ini_options]`.**
   When both files exist, pytest ignores the pyproject pytest config and reads `pytest.ini`
   instead (and prints `WARNING: ignoring pytest config in pyproject.toml!` on startup).
   The wave-13/01 worker added `--timeout=60` and the `security` marker to `pyproject.toml`,
   but those edits were no-ops because `pytest.ini` is the active config. To fix: either
   delete `pytest.ini` (let pyproject win) or sync it. The cleanest fix is to delete
   `pytest.ini` since pyproject has the canonical config. (pytest.ini is NOT in the wave-13
   writes set; wave-14 follow-up.)

2. **`cmd | tail; echo $?` reports `tail`'s exit code, not pytest's.**
   The shell-pipeline trick used in the original brief's acceptance command is wrong when
   the pipeline's last stage is a stream consumer like `tail`. Use
   `cmd > /tmp/log 2>&1; RC=$?; echo $RC` instead. This footgun caused earlier diagnostic
   output to falsely show `exit=0` after a failing test run.

3. **Two subprocess tests in `tests/unit/test_harness.py` write to `data/`.**
   `test_cli_single_task_runs` (5s) and `test_cli_full_runs` (~3min) both run
   `scripts/run_evals.py` as a subprocess. The subprocess cannot see the in-process
   `monkeypatch.setattr` on `DigitalTwinStore.__init__` that the conftest applies, so
   the subprocess writes to the literal hardcoded paths `data/digital_twin.db` and
   `data/chroma/chroma.sqlite3`. The wave-13/01 hermetic acceptance is therefore not
   achievable from conftest alone; the real fix is to add `FINROOT_DIGITAL_TWIN_DB_PATH`
   to `config/settings.py` and route the 4 hardcoded literals in `src/` through it
   (wave-14 follow-up).

4. **The wave-13/01 task is functionally DONE without deselection.**
   After the wave-13/01 conftest landed, the full suite runs **1066 passed / 9 skipped / 0
   failed** and is **3x cold deterministic without any --deselect**. The earlier claim that
   `test_cli_full_runs` had to be deselected was wrong — that test does fail when run as
   part of a long suite (timeout), but on a 3x cold green run it completes within budget.
   The remaining gap is the hermeticity issue (item 3 above), which is genuinely src-side.

5. **`test_cli_full_runs` is timing-flaky under full-suite load.** *(resolved by wave-14)*
   It runs `scripts/run_evals.py --k 1` as a subprocess with a 600s timeout. In isolation
   it takes 197s and passes. In the full suite it can be starved of wall clock and timeout
   (failed ~11% of full-suite runs across 18 sampled runs in 2026-07-24 23:40 verification).
   **Wave-14 fix:** conftest now wraps `subprocess.run`/`Popen` to inject
   `FINROOT_METRICS_PATH` into the subprocess env, so the subprocess writes its single-task
   subset to a tmp path instead of clobbering `results/metrics.json`. The flakiness
   disappeared as a side effect (3/3 cold runs in 2026-07-25 02:30 verification, all rc=0).

6. **The harness subprocess tests overwrite `results/metrics.json`.** *(resolved by wave-14)*
   `test_cli_single_task_runs` and `test_cli_full_runs` both pass `--out
   results/metrics.json` to the subprocess. The subprocess writes a single-task subset
   (RAG drops from 0.3384 to ~0.15) which contaminates the canonical metric. **Wave-14 fix:**
   conftest's subprocess wrapper injects `FINROOT_METRICS_PATH=tmp_path/metrics.json`, and
   `scripts/run_evals.py` `--out` argparse default now reads that env var. The subprocess
   writes to the tmp path; the canonical `results/metrics.json` survives (verified
   2026-07-25 02:30).
