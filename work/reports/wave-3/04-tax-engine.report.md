# Report wave-3/04 — Indian Tax Engine (Deterministic)

## Result
DONE

## What I built
- `src/finroot/tools/tax.py` — TaxRuleTool with typed Input/Output (Pydantic v2, extra="forbid"), deterministic FY 2024-25 capital gains tax calculator. Supports LTCG_EQUITY (10% > ₹1L exempt), STCG_EQUITY (15% flat), STCG (slab rate via annual_income). Surcharge (10% if income > ₹50L), 4% cess optional.
- `data/tax_rules.json` — already existed with correct structure (no changes needed).
- `tests/unit/test_tools_tax.py` — 26 tests covering all hand-computed known values, surcharge, cess=False, negative gain error, invalid gain_type error, TTL cache, audit emission, output shape, determinism.

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_tools_tax.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/srujansai/Desktop/FinRoot
configfile: pytest.ini
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, langsmith-0.8.18, anyio-4.13.0
collected 26 items

tests/unit/test_tools_tax.py ..........................                  [100%]

============================== 26 passed in 7.53s ==============================

$ ruff check src/finroot/tools/tax.py
All checks passed!
```

## Tests
- 26 tests in `tests/unit/test_tools_tax.py` · 26/26 pass
- Coverage: LTCG/STCG/STCG_EQUITY paths, surcharge, cess toggle, zero/negative/invalid gain, TTL cache, audit, determinism, output shape, validation, extra="forbid"

## Decisions / deviations
- `TaxRuleTool` does not support mock/live mode distinction because the task says it's always available (no external API). No `mock` constructor arg needed — rules are always loaded from the JSON file. This is simpler than MarketDataTool's pattern but still honours the BaseTool contract.
- Surcharge threshold is read from the matched rule's `surcharge_threshold` (5000000 for all three rules) to keep the data-driven design. The task's global "₹50L" matches.
- Cess applied as 4% of (base_tax + surcharge), matching the task spec "cess on tax + surcharge".
- Negative gain and unknown gain_type raise `ToolError` (FM-11). The base class wraps these in `ToolCallError`; tests catch both.

## Surprises / gotchas
- N/A

## Follow-ups (for orchestrator triage — do NOT build now)
- Could extend to support old tax regime slabs, 80C deductions, or FY 2025-26 rules in a future wave.

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tool outputs cited (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
