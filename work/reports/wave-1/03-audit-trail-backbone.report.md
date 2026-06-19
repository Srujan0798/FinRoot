# Report wave-1/03 — Hash-Chained Audit Backbone

## Result
DONE

## What I built
- `src/finroot/audit/__init__.py` — already existed (minor ruff fixes: import sorting, combined `with`)
- `src/finroot/audit/trail.py` — already existed (fixed `!d` f-string conversion, `type` shadowing bug)
- `src/finroot/audit/store.py` — already existed (ruff auto-fixed import sorting and nested `with`)
- `tests/unit/test_audit_chain.py` — created: 24 tests covering append, verify, tamper-evidence, replay, store

## Acceptance evidence (real output, this session)
```
$ ruff check src/finroot/audit/
All checks passed!

$ pytest tests/unit/test_audit_chain.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 24 items

tests/unit/test_audit_chain.py ........................                  [100%]

============================== 24 passed in 0.25s ==============================
```

## Tests
- 24 tests added · 24 passed · 0 failed
- Coverage: append (6 tests), verify_chain (6 tests), tamper-evidence (included in verify), replay (6 tests), JsonlAuditStore (6 tests)

## Decisions / deviations
- Fixed 3 bugs in pre-existing code:
  1. `trail.py:103` — `!d` invalid f-string conversion → removed (used `!r` style)
  2. `trail.py:234` — `type(payload).__name__` failed because parameter `type` shadows built-in → changed to `payload.__class__.__name__`
  3. Ruff auto-fixed: import sorting in `store.py`, combined nested `with` statements, `SIM113` noqa for validation counter

## Surprises / gotchas
- Added to `docs/waves/wave-1-gotchas.md`: G-2 (parameter `type` shadows built-in in f-string)

## Follow-ups (for orchestrator triage — do NOT build now)
- Consider renaming `AuditTrail.append(type=...)` parameter to `event_type` to avoid shadowing built-in
- Streaming verifier for chains with >10K events (mentioned in trail.py docstring)

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
