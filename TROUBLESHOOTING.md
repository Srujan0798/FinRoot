# Troubleshooting

Common issues and fixes when developing with FinRoot.

---

## Import Errors

### `ModuleNotFoundError: No module named 'finroot'`

**Cause:** `PYTHONPATH` not set when running standalone Python commands outside pytest.

**Fix:**
```bash
PYTHONPATH=src python3 -m interface.cli --mock "question"
# or
PYTHONPATH=src python3 scripts/smoke_test.py
```

pytest handles this automatically via `pyproject.toml` (`pythonpath = ["src"]`).

### `ImportError: cannot import name 'answer' from 'interface.core'`

**Cause:** Missing `interface.core` module (usually a partial checkout or build issue).

**Fix:** Ensure `src/interface/core.py` exists. Run `make install` to reinstall.

### `ModuleNotFoundError: No module named 'config.settings'`

**Cause:** Running from wrong directory or missing `config/` in path.

**Fix:** Always run from the repository root. The `config` package is importable from root via `pyproject.toml` settings.

---

## Pytest Collection Issues

### `ERROR: no tests ran`

**Cause:** Wrong working directory or `PYTHONPATH` issue.

**Fix:**
```bash
# From repo root:
pytest tests/
# or
make test
```

### `PytestUnknownMarkWarning: Unknown marker: 'slow'`

**Cause:** Older pytest version missing custom marker registration.

**Fix:** Upgrade pytest: `pip install -U pytest`

### Tests fail with `KeyError` for DigitalTwin

**Cause:** Tests are hitting a real SQLite database instead of the test fixture.

**Fix:** Tests use temporary directories. Ensure no leftover `data/` files from a previous run:
```bash
rm -rf data/digital_twin.db data/digital_twin.db.json
```

---

## API Key Configuration

### `NewsSearchTool requires FINROOT_NEWSAPI_KEY`

**Cause:** Live news search without the required API key.

**Fix:** Either set the key or use mock mode:
```bash
export FINROOT_NEWSAPI_KEY=your_key_here
# or
export FINROOT_LLM_PROVIDER=mock
```

### `FINROOT_GROQ_API_KEY is not set`

**Cause:** Provider set to `groq` but no API key configured.

**Fix:**
```bash
export FINROOT_GROQ_API_KEY=gsk_...
# or switch to mock:
export FINROOT_LLM_PROVIDER=mock
```

### API keys appearing in logs/output

**Cause:** Environment variables leaked to output.

**Fix:** FinRoot's mock mode saves/restores `FINROOT_LLM_PROVIDER`. If you see keys in output, check that no custom logging captures env vars. The codebase never prints API keys.

---

## Mock Mode Not Working

### Prices change between runs in mock mode

**Cause:** Python's built-in `hash()` is randomized per process (`PYTHONHASHSEED`).

**Fix:** FinRoot's market tool uses SHA-256 for deterministic hashes. If mock prices still vary, ensure you're using `MarketDataTool` (not a raw `hash()` call). The tool is deterministic across processes and platforms.

### `ToolError: yfinance` not installed

**Cause:** Live mode attempted without `yfinance`.

**Fix:** Either install yfinance or use mock mode:
```bash
pip install yfinance
# or
export FINROOT_LLM_PROVIDER=mock
```

### Mock mode still calls external APIs

**Cause:** Some tools check `FINROOT_LLM_PROVIDER` env var at runtime, not just at import time.

**Fix:** Set the env var before importing:
```bash
FINROOT_LLM_PROVIDER=mock python3 -m interface.cli "question"
```

---

## Slow Test Performance

### Full test suite takes > 10 minutes

**Cause:** The `@pytest.mark.slow` tests are subprocess-based CLI integration tests (5–10 min alone).

**Fix:** Skip slow tests during development:
```bash
make test-fast        # skips @pytest.mark.slow
pytest -m 'not slow'  # equivalent
```

### Tests are slow overall

**Cause:** ChromaDB initialization or large test fixtures.

**Fix:** Use the fast test path. The TF-IDF fallback is faster than ChromaDB for unit tests. If ChromaDB is slow to initialize, ensure `data/chroma/` doesn't have stale data:
```bash
rm -rf data/chroma/
```

---

## Memory and Disk Issues

### `data/digital_twin.db` is locked

**Cause:** SQLite concurrent access from multiple processes.

**Fix:** SQLite is single-writer. Ensure only one FinRoot process accesses the DB at a time. For development, the JSON fallback at `data/digital_twin.db.json` avoids this entirely.

### Disk usage growing

**Cause:** ChromaDB persist directory and audit logs accumulate.

**Fix:**
```bash
# Clear ChromaDB (will be recreated)
rm -rf data/chroma/

# Clear audit logs
rm -f logs/audit.jsonl

# Clear all generated data (keeps source)
make clean
```

### `PermissionError` on macOS for SQLite

**Cause:** File system permissions on `data/` directory.

**Fix:**
```bash
chmod -R u+w data/
# or recreate the directory
rm -rf data/ && mkdir -p data/
```

---

## Docker Issues

### `docker compose up` fails to build

**Cause:** Missing Docker or docker-compose.

**Fix:**
```bash
docker --version  # ensure Docker is installed and running
docker compose up --build
```

### Streamlit UI not accessible at `localhost:8501`

**Cause:** Port conflict or container not started.

**Fix:**
```bash
docker compose down
docker compose up --build
# Wait for "You can now view your Streamlit app in your browser"
```

---

## Linting and Formatting

### `ruff check` reports errors

**Fix:**
```bash
ruff check src/ tests/ --fix   # auto-fix what's safe
ruff format src/ tests/        # format
```

### `ruff format` changes files but CI fails

**Cause:** Pre-commit hook runs `ruff-format` but local formatting differs.

**Fix:** Run the full quality gate before committing:
```bash
make ci
```

---

## Circular Import Errors

### `ImportError: cannot import X from Y which is not fully initialized`

**Cause:** Circular import between `config.settings` and `finroot.*`.

**Fix:** `config/settings.py` must NEVER import from `finroot.*`. This is a design rule (G-1). If you see this error, check that `config/settings.py` only uses `pydantic_settings` imports.

---

## Evaluation Issues

### `make evals` returns stale metrics

**Cause:** `results/metrics.json` not regenerated.

**Fix:**
```bash
make evals           # regenerate
make validate-docs   # check docs cite current metrics
```

### `metrics.json` is missing

**Cause:** Never generated or was cleaned.

**Fix:**
```bash
make evals
```

---

## Getting Help

- Run `make doctor` to smoke-check all integrations
- Run `make session-start` for a one-page context summary
- Check `docs/` for architecture and decision records
- See `CONTRIBUTING.md` for development workflow
