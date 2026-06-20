# Task wave-1/07 — Mock Provider Expansion (50+ canned responses)

> Read `work/WORKER_PROMPT.md` then build. Upgrades the mock LLM from 5 to 50+ responses.

## Objective
Expand the MockProvider from 5 canned responses to 50+ covering all financial domains, so the offline demo shows rich variety instead of repeating the same 5 answers.

## Writes (ONLY these)
- `src/finroot/llm/mock.py` (UPDATE — expand response pool)
- `tests/unit/test_llm_provider.py` (UPDATE — adjust variety assertions)

## Forbid
All other files.

## Steps
1. Read existing `src/finroot/llm/mock.py` — understand the hash-based rotation mechanism.
2. Expand `_MOCK_RESPONSES` list from 5 to 50+ entries covering:
   - Portfolio analysis (8+): allocation review, rebalancing, diversification, concentration risk
   - Risk assessment (8+): VaR interpretation, drawdown analysis, volatility, beta, Sharpe
   - Tax planning (8+): LTCG, STCG, capital gains optimization, 80C, NPS, tax harvesting
   - News/market impact (6+): RBI policy, budget impact, global events, sector rotation
   - Cashflow (4+): emergency fund, SIP planning, debt management
   - Credit (4+): credit score, loan optimization, EMI management
   - General (4+): goal-based planning, insurance adequacy, retirement
   - Each response must include `<reasoning>` and `<confidence>` tags (the parser expects them)
   - Each response should be 3-5 sentences, realistic, with specific numbers
3. Update test: verify that 50+ distinct responses exist and rotation works.

## Acceptance
```bash
PYTHONPATH=src:. python3 -c "
from finroot.llm.mock import MockProvider
p = MockProvider()
texts = set()
for i in range(100):
    r = p.complete(f'test query {i}')
    texts.add(r.text[:50])
print(f'{len(texts)} distinct responses in 100 calls')
assert len(texts) >= 20, f'Expected 20+ distinct, got {len(texts)}'
print('variety OK')
"
PYTHONPATH=src:. python3 -m pytest tests/unit/test_llm_provider.py -v
```

## Report
`work/reports/wave-1/07-mock-expansion.report.md`
