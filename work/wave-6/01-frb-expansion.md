# Task wave-6/01b — FRB Question Bank Expansion (50+ total)

> Read `work/WORKER_PROMPT.md` then build. Extends the existing 32-question bank.

## Objective
Expand the FRB question bank from 32 to 50+ questions, adding coverage for insurance, estate planning, behavioral biases, international diversification, and more adversarial traps.

## Writes (ONLY these)
- `data/gold/frb_questions.json` (REPLACE — merge existing + new)
- `tests/unit/test_frb_bank.py` (UPDATE — adjust count assertions)

## Forbid
All other files.

## Contract
Read `.specify/specs/wave-6/contracts/evals.contract.md` § FRB task shape. Match EXACTLY.

## Steps
1. Read existing `data/gold/frb_questions.json` (32 questions).
2. Add 20+ new questions to reach 50+ total. New domains to add:
   - insurance (≥3): health insurance adequacy, term life vs ULIP, claim rejection traps
   - estate_planning (≥2): nomination pitfalls, succession planning
   - behavioral (≥3): loss aversion, recency bias, herd mentality in investing
   - international (≥2): currency risk, LRS limits, diversification into US markets
   - More traps (≥4): "guaranteed 20% returns", "borrow to invest in F&O", "put all savings in one stock", "ignore insurance to invest more"
3. Keep existing 32 questions UNCHANGED (don't break working graders).
4. Update `tests/unit/test_frb_bank.py`: change minimum count assertion from 24 to 50.
5. Run acceptance: `PYTHONPATH=src:. python3 -m pytest tests/unit/test_frb_bank.py -v`

## Acceptance
```bash
PYTHONPATH=src:. python3 -c "import json; q=json.load(open('data/gold/frb_questions.json')); print(f'{len(q)} questions, domains:', sorted({x['domain'] for x in q}))"
PYTHONPATH=src:. python3 -m pytest tests/unit/test_frb_bank.py -v
```

## Report
`work/reports/wave-6/01-frb-expansion.report.md`
