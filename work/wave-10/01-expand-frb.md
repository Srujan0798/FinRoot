# Task wave-10/01 — Expand FRB to 80+ Questions

> Read `work/WORKER_PROMPT.md` then build. Highest-leverage upgrade.

## Objective
Expand `data/gold/frb_questions.json` from 52 to 80+ questions. Add coverage in weak domains
(news_impact, cashflow, estate_planning, insurance) and add more numeric/tax questions with
deterministic answers. Every question must match the existing JSON schema exactly.

## Writes (ONLY these)
- `data/gold/frb_questions.json` (append 30+ new questions to existing 52)
- `tests/unit/test_frb_bank.py` (update counts: min 80 items)

## Forbid
All other files.

## Steps
1. Read existing `data/gold/frb_questions.json` — get the schema and existing IDs (frb-001 to frb-052).
2. Add 30+ new questions (frb-053 to frb-082+) with:
   - Domain coverage: news_impact (4+), cashflow (4+), estate_planning (3+), insurance (3+), international (3+), behavioral (3+), credit (3+), general (3+), portfolio (3+), risk (3+), tax (4+)
   - Difficulty spread: ~10 easy, ~12 medium, ~8 hard
   - At least 8 new adversarial trap questions (must_not non-empty)
   - Tax questions with numeric_answer (Indian FY2024-25 rules): LTCG equity 10% > ₹1L, STCG equity 15%, debt LTCG 20% with indexation, etc.
   - Twin IDs reference existing profiles (twin_priya_sharma_001, twin_rahul_mehta_002, twin_ananya_iyer_003) or null
   - must_mention keywords: 3-5 per question, specific enough to verify
   - min_citations: 1-3 per question
3. Update `tests/unit/test_frb_bank.py`: change minimum count from 52 to 80.

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_frb_bank.py -v
python3 -c "import json; q=json.load(open('data/gold/frb_questions.json')); print(f'{len(q)} questions, domains:', sorted({x['domain'] for x in q}))"
```

## Report
`work/reports/wave-10/01-expand-frb.report.md`
