# Wave 3 Gotchas

> Captured DURING the wave, not after. Workers append surprises here as they hit them.

## Pre-loaded warnings (from design phase — avoid these)
*(none yet for wave 3)*

## Gotchas hit during the wave
*(append as you go — format below)*
```
### G-N: <title>
- Hit by: task 0X
- Workaround: ...
- Permanent fix needed: Y/N → (rule/ADR/test added?)
```

### G-3.5: `BaseTool` retry backoff slows down tests that expect loud failure
- Hit by: task 05 (macro + currency)
- `BaseTool.__call__` retries failed `_run` up to `max_retries=3` times with
  exponential backoff (`base_delay=1.0` → 1+2+4 = 7 s of sleeps per failing
  test). A whole file of "expected-failure" tests therefore takes minutes.
- Workaround (in test code): on the test tool instance, set
  `tool.base_delay = 0.001` and `tool.max_retries = 0` so the loud failure
  propagates on the first attempt. The retry mechanism itself is covered
  by `tests/unit/test_base_interfaces.py::TestBaseToolLoudFailure`.
- Permanent fix needed: N → workaround is local and clear; leaving the
  production defaults at 1 s / 3 retries is the right call for live APIs.
