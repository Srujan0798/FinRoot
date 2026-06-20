# Task wave-11/04 — Security Tests + Input Validation

> Read `work/WORKER_PROMPT.md` then build. Shows security awareness.

## Objective
Add security tests that verify input validation, injection prevention, and safe error handling.
This shows judges the system is production-ready and security-conscious.

## Writes (ONLY these)
- `tests/security/__init__.py`
- `tests/security/test_input_validation.py`
- `tests/security/test_injection_prevention.py`

## Forbid
`src/**` (import only), `evals/**`, `data/gold/**`.

## Steps
1. `tests/security/test_input_validation.py` (8+ tests):
   - Empty query handled gracefully
   - Very long query (>10000 chars) handled gracefully
   - SQL injection attempt in query
   - Script injection attempt in query
   - Special characters in query (unicode, emojis, etc.)
   - Invalid tool output format
   - Invalid recommendation format
   - Invalid audit event format
2. `tests/security/test_injection_prevention.py` (6+ tests):
   - Prompt injection attempt in query
   - Tool output injection attempt
   - Citation injection attempt
   - Audit event injection attempt
   - Memory injection attempt
   - Twin profile injection attempt
3. Each test should verify the system handles the input gracefully (no crashes, no data leaks).
4. Use `@pytest.mark.security` marker.

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/security/ -v -m security
ruff check tests/security/
```

## Report
`work/reports/wave-11/04-security-tests.report.md`
