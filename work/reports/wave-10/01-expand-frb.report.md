# Report wave-10/01 — Expand FRB to 80+ Questions

## Result
DONE

## What I built
- `data/gold/frb_questions.json` — appended 31 new questions (frb-053 to frb-083), expanding from 52 to 83 total
- `tests/unit/test_frb_bank.py` — updated minimum count assertion from 50 to 80

## Acceptance evidence (real output, this session)
```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_frb_bank.py -v
============================= test session starts ==============================
collected 27 items

tests/unit/test_frb_bank.py ...........................                  [100%]

============================= 27 passed in 0.18s ==============================

$ python3 -c "import json; q=json.load(open('data/gold/frb_questions.json')); print(f'{len(q)} questions, domains:', sorted({x['domain'] for x in q}))"
83 questions, domains: ['behavioral', 'cashflow', 'credit', 'estate_planning', 'general', 'insurance', 'international', 'news_impact', 'portfolio', 'risk', 'tax']

$ ruff check tests/unit/test_frb_bank.py
All checks passed!
```

## Domain coverage (83 questions)
- behavioral: 7
- cashflow: 6
- credit: 6
- estate_planning: 5
- general: 8
- insurance: 7
- international: 4
- news_impact: 9
- portfolio: 10
- risk: 9
- tax: 12

## Difficulty spread
- easy: 24
- medium: 31
- hard: 28

## Adversarial traps (low confidence + refusal keyword in must_mention): 7
(frb-028, frb-029, frb-030, frb-031, frb-040, frb-044, frb-045)

## New questions with numeric_answer (tax determinism)
- frb-072: HRA exemption = ₹2,52,000 (metro, 50% test)
- frb-073: LTCG ₹3L = ₹20,800 (10% on ₹2L + cess)
- frb-074: Debt fund LTCG with indexation = ₹41,600
- frb-075: NPS 80CCD(1B) tax saving = ₹15,600
- frb-076: Section 80D deduction = ₹45,000

## New twin references
- frb-054: twin_rahul_mehta_002 (cashflow/EMI affordability)
- frb-059: twin_rahul_mehta_002 (insurance/endowment switch)
- frb-061: twin_priya_sharma_001 (news_impact/tax harvesting)
- frb-063: twin_ananya_iyer_003 (international/REIT tax)
- frb-065: twin_priya_sharma_001 (behavioral/recency bias)
- frb-070: twin_rahul_mehta_002 (portfolio/rebalancing)
- frb-078: twin_ananya_iyer_003 (news_impact/SEBI regulation)
- frb-081: twin_priya_sharma_001 (general/portfolio review)

## Tests
- 27 tests · all passing · 0 failures
- No new tests added (existing test suite already covers the expanded bank)

## Decisions / deviations
- Added 31 questions (frb-053 to frb-083) instead of minimum 30 to overshoot the 80 threshold comfortably
- New tax questions (frb-072 to frb-076) cover HRA, LTCG, debt-fund indexation, NPS 80CCD(1B), and Section 80D — not in the TaxRuleTool cross-check scenarios dict (which only covers capital gains). These are manually computed and verified in the rationale field.
- The test's trap definition (confidence=low + refusal keyword in must_mention) identifies 7 traps total. The task's definition ("must_not non-empty") covers all 31 new questions. The test's `test_at_least_4_traps` passes with 7.
- All new questions use the existing twin profiles (twin_priya_sharma_001, twin_rahul_mehta_002, twin_ananya_iyer_003) or null.

## Surprises / gotchas
- None. No gotchas to append.

## Follow-ups (for orchestrator triage — do NOT build now)
- Consider adding frb-072 to frb-076 (HRA/NPS/80D tax questions) to the TaxRuleTool cross-check scenarios dict in test_frb_bank.py for full numeric verification coverage
- The test's trap detection could be broadened to also count questions with `expected_confidence == "low"` that have strong refusal language in `must_not` (even without "do not act yet" in `must_mention`)

## Self-check
- [x] Only touched my Writes set (no collisions, FM-13)
- [x] No fabricated numbers; tax computations manually verified in rationale (FM-11)
- [x] No bare excepts / silent fallbacks
- [x] ruff clean, tests green (output above)
- [x] No secrets committed (FM-07)
