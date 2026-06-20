# Task wave-3/04 — Indian Tax Engine (Deterministic)

> Read `work/WORKER_PROMPT.md` then build. Parallel with other wave-3 tasks.

## Objective
A deterministic, unit-tested Indian capital gains tax calculator (FY 2024-25 rules).
No live API — rules stored in `data/tax_rules.json`. This is the "show your math" tool for
financial explainability; every output cites the rule applied.

## Writes (ONLY these)
- `src/finroot/tools/tax.py`
- `data/tax_rules.json`
- `tests/unit/test_tools_tax.py`

## Forbid
All other `src/finroot/tools/` files. Do NOT modify `src/finroot/schemas/`.

## Contract
Read `.specify/specs/wave-3/contracts/tools.contract.md` § TaxRuleTool.

## Tax rules to implement (FY 2024-25)
- **LTCG equity** (held > 12 months): 10% on gains above ₹1,00,000 exempt limit; 4% cess on tax.
- **STCG equity** (`STCG_EQUITY`, held ≤ 12 months): 15% flat; 4% cess.
- **STCG other** (`STCG`, debt/gold/others): taxed at slab rate (pass `annual_income` for slab).
- Indian IT slabs (FY 2024-25 new regime): 0% up to ₹3L, 5% ₹3-7L, 10% ₹7-10L, 15% ₹10-12L, 20% ₹12-15L, 30% above ₹15L.
- Surcharge: 10% if income > ₹50L (on income tax, not gain tax — apply when `annual_income > 5000000`).
- `cess = True` adds 4% health & education cess on tax + surcharge.

## Steps
1. `data/tax_rules.json` — structured rules file:
   ```json
   {"rules": [{"id": "LTCG_EQUITY", "rate": 0.10, "exemption": 100000, "cess": 0.04, "description": "..."},...]}
   ```
2. `TaxRuleTool(BaseTool)`:
   - Load rules from `data/tax_rules.json` once at init.
   - Compute tax step-by-step; populate `breakdown` dict with every component.
   - `rule_applied` = human-readable rule name + citation.
   - No external API; always available (no Mock/live distinction needed, but honour BaseTool structure).
3. Tests (minimum 16) — known values (hand-computed):
   - LTCG ₹2L gain: exempt ₹1L → tax on ₹1L = ₹10,000 + cess ₹400 = ₹10,400
   - LTCG ₹50,000 gain: fully exempt → ₹0
   - STCG_EQUITY ₹1L: 15% = ₹15,000 + cess ₹600 = ₹15,600
   - STCG (debt) for income ₹8L: slab 10% = ₹10,000 + cess ₹400
   - Surcharge kicks in for income > ₹50L
   - Invalid gain_type raises ToolError (FM-11)
   - Negative gain raises ToolError
   - cess=False omits cess

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_tools_tax.py -v
ruff check src/finroot/tools/tax.py
```
All test cases must match hand-computed expected values exactly (deterministic rule engine).

## Report
`work/reports/wave-3/04-tax-engine.report.md`
