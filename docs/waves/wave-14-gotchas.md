# wave-14 gotchas

## 01 — Env-Var Hermeticity + Metrics Contamination Fix

### 1. `test_tools_profile.py::profiles_path` fixture creates `data/digital_twin.db` regardless of conftest monkeypatch. *(resolved by wave-15/iter1)*

The `profiles_path` fixture (in `tests/unit/test_tools_profile.py`) used to do:

```python
saved = sys.modules.pop("finroot.memory.digital_twin", None)
yield p
if saved is not None:
    sys.modules["finroot.memory.digital_twin"] = saved
```

This popped the module from `sys.modules` to force `UserProfileTool._load_profile` to take the JSON-fallback path. But the side effect was that the re-imported `finroot.memory.digital_twin` is a **fresh module** with the original (unpatched) `DigitalTwinStore.__init__` — the conftest's `monkeypatch.setattr` on the class `__init__` was lost. When `UserProfileTool._load_profile` did `from finroot.memory.digital_twin import DigitalTwinStore; store = DigitalTwinStore()`, the `DigitalTwinStore()` call used the default `db_path="data/digital_twin.db"` and created the file in the repo root.

**Resolved 2026-07-25 (wave-15/iter1):** replaced `sys.modules.pop` with `monkeypatch.setattr(finroot.memory.digital_twin, "DigitalTwinStore", _raise)` and `monkeypatch.setattr(..., "DigitalTwin", _raise)`. The function-local imports inside `_load_profile` and `_save_profile` bind to our raising class, the `except (ImportError, Exception)` clause catches it, and the JSON fallback runs. The class `__init__` monkeypatch is preserved (no module re-import). Verified: `rm -rf data/digital_twin.db && pytest --timeout=120` produces no `data/digital_twin.db` (full suite, 1069 passed / 9 skipped / 0 failed).

### 2. Setting `FINROOT_CHROMA_DIR` in the conftest breaks `test_config.py::test_default_paths`

`tests/unit/test_config.py::TestSettingsDefaults::test_default_paths` asserts:

```python
s = Settings()
assert s.chroma_dir == "data/chroma"
```

`Settings()` is a `pydantic_settings.BaseSettings` subclass that reads `FINROOT_*` env vars at construction. If the conftest sets `FINROOT_CHROMA_DIR` in the autouse fixture, the test fails because `s.chroma_dir` becomes the tmp path.

**Resolution in wave-14/01:** the conftest does NOT set `FINROOT_CHROMA_DIR` in the parent's env. Instead, a `subprocess.run` / `subprocess.Popen` wrapper (installed at conftest load) injects `FINROOT_CHROMA_DIR` into the subprocess env only. The parent process's env is untouched, so `test_config.py` passes. The subprocess (which has fresh Python modules and no in-process monkeypatch) reads the injected env var via `get_settings().chroma_dir` and writes to the tmp path.

For `FINROOT_DIGITAL_TWIN_DB`, the fixture does set it (per the brief) — this is safe because no test asserts the default for the new `digital_twin_db` field.

### 3. Brief's `--timeout=30` is too short for the full suite

`test_cli_full_runs` runs the full FRB bank (83 tasks × 3 systems with `--k 1` = 249 trials), which takes ~30-60 seconds. The brief's acceptance script uses `--timeout=30`, which kills the test intermittently. With `--timeout=60` (from pyproject.toml), it passes most of the time. With `--timeout=120` (used in the wave-14/01 report), it passes consistently. The brief's acceptance script needs `--timeout=120` or higher to be reliable.

### 4. Brief's `FINROOT_DIGITAL_TWIN_DB_PATH` naming

The brief says to set `FINROOT_DIGITAL_TWIN_DB_PATH`, but the `Settings` field is `digital_twin_db` with env_prefix `FINROOT_` → env var `FINROOT_DIGITAL_TWIN_DB` (no `_PATH` suffix). wave-14/01 uses `FINROOT_DIGITAL_TWIN_DB` to match the pydantic-settings field name.
