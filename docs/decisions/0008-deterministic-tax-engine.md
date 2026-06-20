# ADR-0008 — Deterministic tax engine

- **Status:** Accepted
- **Date:** 2026-06-20
- **Deciders:** Orchestrator (with Srujan)

## Context
Financial advice requires deterministic, auditable calculations. We need:

1. **No fabricated data:** All numbers must come from tools and be cited (FM-11)
2. **Reproducible results:** Same inputs always produce same outputs
3. **Transparent rules:** Tax calculations must be explainable
4. **Evidence:** Every calculation must cite the rule applied (FM-09)

## Decision
We implemented **Deterministic tax engine** in `src/finroot/tools/tax.py`:

The tax engine:
- Uses rule-based logic (not LLM) for calculations
- Loads rules from `data/tax_rules.json` (FM-11)
- Returns structured output with full breakdown
- Cites every rule applied

Key design decisions:
- **Rule-based:** No LLM hallucinations; deterministic results
- **JSON rules:** Easy to audit and modify
- **Structured output:** Full breakdown for transparency
- **Citations:** Every rule is cited (FM-09)

The engine ensures:
- **FM-11:** No fabricated financial data; all numbers come from rules
- **FM-09:** Evidence required; each calculation cites the rule
- **FM-07:** No secrets; rules are in version control

Example output structure:
```json
{
  "tax_amount": 12345.67,
  "effective_rate_pct": 15.2,
  "breakdown": {
    "base_tax": 10000.0,
    "cess": 1234.56,
    "surcharge": 111.11
  },
  "rule_applied": "LTCG slab 10% + 4% cess",
  "citation": "data/tax_rules.json rule #3"
}
```

## Consequences
- **Positive:** Judges can verify tax calculations (FM-09)
- **Positive:** No LLM hallucinations; deterministic results (FM-11)
- **Positive:** Transparent and auditable calculations
- **Negative:** Rules must be maintained and updated
- **Negative:** Less flexible than LLM-based calculations
- **Neutral:** Adds complexity but is essential for financial accuracy

## Alternatives considered
- **LLM-based tax calculation:** Risk of hallucinations; hard to audit
- **Hardcoded formulas:** Hard to maintain and modify
- **External tax APIs:** Dependencies on external services; potential costs

The deterministic tax engine is the minimal design that delivers accurate, auditable, and reproducible tax calculations for financial advice.