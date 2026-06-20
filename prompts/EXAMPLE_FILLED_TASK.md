# Example — a filled task file + report (reference for workers)

> A worked example so workers see the expected shape and rigor. Based on a hypothetical wave-3 tool.

## The task (as dispatched) — work/wave-3/0X-currency-tool.md
**Objective:** Implement `CurrencyConverterTool` on `BaseTool`: convert an amount between currencies
using a keyless FX source, cached + rate-limited, failing loud on an unknown currency.
**Writes:** `src/finroot/tools/currency.py`, `tests/unit/test_currency_tool.py`
**Forbid:** everything else; import `BaseTool` from `src/finroot/tools/base.py`.
**Acceptance:**
```bash
ruff check src/finroot/tools/currency.py
pytest tests/unit/test_currency_tool.py -v
```

## The report (as returned) — work/reports/wave-3/0X-currency-tool.report.md
**Result:** DONE
**What I built:** `currency.py` (CurrencyConverterTool, typed In/Out, TTL cache, loud-fail on bad code),
`test_currency_tool.py` (6 tests).
**Acceptance evidence:**
```
$ ruff check src/finroot/tools/currency.py
All checks passed!
$ pytest tests/unit/test_currency_tool.py -v
... 6 passed in 0.31s
```
**Decisions:** chose exchangerate.host (keyless) as the source; cache TTL 1h.
**Surprises:** unknown currency must raise, not return 0 — added a test (FM-11). Logged to wave-3-gotchas.
**Self-check:** [x] only my Writes set · [x] numbers cited (FX rate from tool) · [x] no silent fallback ·
[x] ruff clean, tests green · [x] no secrets.

> Note the rigor: real command output, explicit decisions, a loud-fail test, and the self-check ticked.
