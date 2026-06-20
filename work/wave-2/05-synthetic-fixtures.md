# Task wave-2/05 — Synthetic Digital Twin Fixtures & Sample Data

> Read `work/WORKER_PROMPT.md` then build. Can run in parallel with 01-03; needs 03 schema.

## Objective
Create 3 sample DigitalTwin profiles and a sample conversation fixture for use in tests, demos,
and the FRB reasoning benchmark. All data must be clearly synthetic (no real PII).

## Writes (ONLY these)
- `data/samples/twin_profiles.json`
- `data/samples/README.md`
- `data/synthetic/sample_conversation.json`

## Forbid
All `src/` files. All `tests/` files.

## Contract
Read `.specify/specs/wave-2/contracts/memory.contract.md` § Synthetic fixtures.
Read `src/finroot/memory/digital_twin.py` to get exact field names (if task 03 is done) or use the contract schema.

## Steps
1. `data/samples/twin_profiles.json` — JSON array of 3 DigitalTwin-compatible dicts:
   - Profile A "Priya Sharma": conservative, 32, IT professional, medium horizon, INR-heavy portfolio
   - Profile B "Rahul Mehta": moderate, 45, business owner, mixed goals, moderate holdings
   - Profile C "Ananya Iyer": aggressive, 27, startup employee, ESOP-heavy, long horizon
   - Each has: user_id, name, age, risk_tolerance, investment_horizon, monthly_income, monthly_expenses, tax_bracket_pct, goals (3+), constraints (2+), holdings (3+ assets), created_at, updated_at
   - Holdings: mix of equity (NSE tickers), MF, FD with realistic Indian INR values

2. `data/synthetic/sample_conversation.json` — 10-turn conversation array:
   - Format: `[{"role": "user"|"assistant", "content": "...", "turn": N}]`
   - Topic: portfolio review + risk assessment for Profile B (Rahul Mehta)
   - Must include: a question with a cited number, a follow-up on risk, a recommendation with confidence label

3. `data/samples/README.md` — brief doc: what each file is, which profile is which archetype, how to load them in tests.

## Acceptance
```bash
python3 -c "
import json
profiles = json.load(open('data/samples/twin_profiles.json'))
assert len(profiles) == 3, f'Expected 3 profiles, got {len(profiles)}'
for p in profiles:
    assert 'user_id' in p and 'name' in p and 'holdings' in p
conv = json.load(open('data/synthetic/sample_conversation.json'))
assert len(conv) == 10, f'Expected 10 turns, got {len(conv)}'
print('fixtures OK')
"
```

## Report
`work/reports/wave-2/05-synthetic-fixtures.report.md`
