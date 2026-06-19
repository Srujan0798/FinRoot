# Wave 1 Gotchas

> Captured DURING the wave, not after. Workers append surprises here as they hit them.

## Pre-loaded warnings (from design phase — avoid these)
### G-0a: Pydantic v2 + `extra="forbid"` rejects `Optional[X]` shorthand quirks
- Use `X | None`, not `Optional[X]`, and set `model_config = ConfigDict(extra="forbid")`.

### G-0b: Optional provider SDKs must be lazy-imported
- `import groq` / `openai` / `chromadb` at module top breaks Mock-only/offline runs. Import inside
  the adapter method so Mock needs zero extras.

### G-0c: Audit canonical JSON must be stable
- Hash over `json.dumps(payload, sort_keys=True, separators=(",",":"))` with UTC ISO timestamps, or
  `verify_chain` will flake across machines.

## Gotchas hit during the wave
*(append as you go — format below)*
```
### G-N: <title>
- Hit by: task 0X
- Workaround: ...
- Permanent fix needed: Y/N → (rule/ADR/test added?)
```

### G-1: `src/finroot/schemas/__init__.py` uses `from finroot.*` imports requiring `src` on PYTHONPATH
- Hit by: task 04 (config-settings)
- `config/settings.py` imports `Provider` from `src.finroot.schemas.enums`, which triggers loading
  `schemas/__init__.py` that does `from finroot.schemas.audit import AuditEvent`. Without `src/` on
  `PYTHONPATH` or installed as package, `finroot` is not a top-level module.
- Workaround: prefix acceptance commands with `PYTHONPATH=src`, or run via pytest (which uses
  `pythonpath = ["src"]` from `pyproject.toml`).
- Permanent fix needed: Y → fix `schemas/__init__.py` to use relative or `src.*` imports so the
  acceptance command works standalone.

### G-3: `config/settings.py` circular import + script `sys.path` missing project root
- Hit by: task 06 (bootstrap)
- `config/settings.py` imported `Provider` from `src.finroot.schemas.enums`; `finroot/__init__.py` re-exported `get_settings` from `config` → circular import at package init time. Also: running `python3 scripts/smoke_test.py` puts `scripts/` on `sys.path[0]` (not project root), so `config/` was not importable.
- Fix applied: `settings.llm_provider` changed to `str = "mock"` (no finroot import in config); `utils/config.py` compares strings directly; `smoke_test.py` inserts project root on `sys.path`.
- Permanent fix needed: N → resolved.

### G-2: Parameter named `type` shadows built-in in f-string
- Hit by: task 03 (audit-trail-backbone)
- In `trail.py:234`, `{type(payload).__name__}` failed with `TypeError: 'str' object is not callable`
  because the function parameter `type: str` shadows the built-in `type()` function.
- Workaround: use `payload.__class__.__name__` instead of `type(payload).__name__`.
- Permanent fix needed: N → local fix applied; consider renaming parameter to `event_type` if
  it causes confusion elsewhere.
