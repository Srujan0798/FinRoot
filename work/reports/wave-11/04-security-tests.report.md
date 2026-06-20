# Report wave-11/04 — Security Tests + Input Validation

## Result
DONE

## What I built
- `tests/security/__init__.py` — package marker
- `tests/security/test_input_validation.py` — 8 test classes, 14 parametrized test methods covering empty queries, long queries, SQL injection, XSS/script injection, special characters (unicode/emoji/null bytes), invalid tool output, invalid recommendation format, invalid audit event format
- `tests/security/test_injection_prevention.py` — 6 test classes covering prompt injection in queries, tool output injection, citation injection, audit event injection, memory injection, and twin profile injection

## Acceptance evidence (real output, this session)
```
$ ruff check tests/security/
All checks passed!

$ PYTHONPATH=src python3 -m pytest tests/security/ -v -m security
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.8.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 100 items

tests/security/test_injection_prevention.py ............................ [ 28%]
.....................                                                    [ 49%]
tests/security/test_input_validation.py ................................ [ 81%]
...................                                                      [100%]

======================= 100 passed, 14 warnings in 0.26s =======================
```

## Tests
- 100 tests total · 100 passed · 0 failed · 0 errors
- 8 test classes in `test_input_validation.py`: TestEmptyQuery, TestVeryLongQuery, TestSQLInjection, TestScriptInjection, TestSpecialCharacters, TestInvalidToolOutput, TestInvalidRecommendation, TestInvalidAuditEvent
- 6 test classes in `test_injection_prevention.py`: TestPromptInjection, TestToolOutputInjection, TestCitationInjection, TestAuditEventInjection, TestMemoryInjection, TestTwinProfileInjection
- All tests marked with `@pytest.mark.security`

## Decisions / deviations
- **Tool output injection**: `AgentState.tool_outputs` is `list[dict]` (not a Pydantic model), so extra keys in individual dicts are accepted. Tests verify injected keys are not promoted to state fields and do not affect pipeline behavior (graceful handling), rather than expecting rejection.
- **Working memory from_json injected fields**: `from_json()` only passes `role` and `content` to `add()`, silently dropping injected fields. Tests verify fields are dropped, not that they raise.
- **pytest.ini marker warning**: `security` marker not registered in `pytest.ini` (not in Writes set). Warnings are cosmetic and do not affect test execution.

## Surprises / gotchas
- Added to docs/waves/wave-11-gotchas.md? N (no surprises beyond the above design observations)

## Follow-ups (for orchestrator triage — do NOT build now)
- Register `security` marker in `pytest.ini` (minor: suppresses 14 pytest warnings)
- Consider adding `extra="forbid"` to `tool_outputs` item schema if stronger validation is desired at the tool-output boundary

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
