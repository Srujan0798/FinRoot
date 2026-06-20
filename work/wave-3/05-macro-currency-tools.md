# Task wave-3/05 — MacroDataTool + CurrencyConverterTool

> Read `work/WORKER_PROMPT.md` then build. Parallel with other wave-3 tasks.

## Objective
Indian macro indicators (GDP growth, inflation, repo rate) from World Bank public API with
Mock canned values, and currency conversion with a live free API + fixed-rate Mock table.

## Writes (ONLY these)
- `src/finroot/tools/macro.py`
- `src/finroot/tools/currency.py`
- `tests/unit/test_tools_macro.py`

## Forbid
All other `src/finroot/tools/` files.

## Contract
Read `.specify/specs/wave-3/contracts/tools.contract.md` § MacroDataTool, § CurrencyConverterTool.

## Steps
1. `MacroDataTool(BaseTool)`:
   - Mock values (always use in mock mode):
     - `gdp_growth` IN: 7.2, unit "% YoY", period "2024"
     - `inflation` IN: 5.1, unit "% CPI YoY", period "2024"
     - `repo_rate` IN: 6.5, unit "%", period "Jun 2024"
     - `unemployment` IN: 7.8, unit "%", period "2024"
   - Live: World Bank API `https://api.worldbank.org/v2/country/{country}/indicator/{wb_code}?format=json&mrv=1` (no key needed).
   - indicator→wb_code mapping: gdp_growth→NY.GDP.MKTP.KD.ZG, inflation→FP.CPI.TOTL.ZG, repo_rate→FM.RBL.BMNY.ZG (best proxy), unemployment→SL.UEM.TOTL.ZS
   - Cache TTL 3600s (macro data is slow-moving).

2. `CurrencyConverterTool(BaseTool)`:
   - Mock fixed table (as of 2026-06): USD/INR=83.5, EUR/INR=90.2, GBP/INR=106.0, JPY/INR=0.56, AED/INR=22.7
   - Live: `https://open.er-api.com/v6/latest/{from_currency}` (free, no key).
   - Cross-rates: compute via INR as base if direct rate not available.
   - Cache TTL 300s.
   - citation: "Exchange rate source: open.er-api.com / Mock fixed-rate table (2026-06)"

3. Tests (minimum 12):
   - Mock macro returns correct values for each indicator
   - Unknown indicator raises ToolError (FM-11)
   - Mock currency USD→INR = 83.5
   - Mock currency EUR→USD = EUR/INR ÷ USD/INR (cross-rate)
   - Currency zero amount handled (returns 0.0, no error)
   - Cache TTL correctly set on both tools

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_tools_macro.py -v
ruff check src/finroot/tools/macro.py src/finroot/tools/currency.py
```

## Report
`work/reports/wave-3/05-macro-currency-tools.report.md`
