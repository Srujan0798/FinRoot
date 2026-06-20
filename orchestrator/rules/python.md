# Rule — Python (applies to `src/**`, `tests/**`, `scripts/**`)

- Python 3.11. Type hints everywhere. **Pydantic v2** for all data crossing a boundary.
- `model_config = ConfigDict(extra="forbid")` on schemas — catch typos at the edge.
- Pydantic v2 gotcha: use `X | None`, not `Optional[X]`, under `extra="forbid"` (see wave gotchas).
- No bare `except:` and no `except: pass`. Catch specific exceptions; log loudly; re-raise or
  return a typed error. NEVER swallow an error or substitute synthetic data (FM-11).
- Numbers in financial outputs come from a tool call and carry a `Citation`. No model-invented figures.
- Functions small and single-purpose. Pure where possible (the reasoning step is a reducer over state).
- Lazy-import optional/heavy deps (chromadb, finbert, provider SDKs) so Mock mode needs nothing extra.
- `ruff` is the linter+formatter (config in `pyproject.toml`). Code must be `ruff check` clean.
- Tests: `pytest`; deterministic; seed all RNG; fresh state per test; Mock provider by default.
- Logging via the project logger (structured), not `print`, except in CLI/scripts user output.
