# Task wave-5/03 — Rooted Prudence Principles Verifier

> Read `work/WORKER_PROMPT.md` then build. Parallel with tasks 01, 04.

## Objective
Implement `PrudentialVerifier` — the financial prudence checklist that ensures advice doesn't
violate basic safety principles. The "do no harm" gate.

## Writes (ONLY these)
- `src/finroot/reasoning/principles.py`
- `tests/unit/test_principles.py`

## Forbid
All other `src/finroot/reasoning/` files.

## Contract
Read `.specify/specs/wave-5/contracts/reasoning.contract.md` § Rooted Prudence Principles.
Read `src/finroot/schemas/state.py` for `AgentState`.

## Steps
1. `PrudentialVerifier`:
   - `verify(state: AgentState) -> PrudentialVerdict`
   - 7 checks from contract:
     1. **Emergency fund**: if answer mentions investing emergency fund → FAIL
     2. **Diversification**: if answer recommends >40% single asset → FAIL
     3. **Risk match**: if advice is aggressive but twin is conservative → FAIL
     4. **No guarantees**: if answer contains "guaranteed", "will definitely", "promise" → FAIL
     5. **Tax awareness**: if recommending sell without mentioning tax → WARN
     6. **Horizon match**: if recommending short-term for long-horizon investor → FAIL
     7. **Insufficient evidence**: if tool_outputs < 2 and answer is specific → FAIL
   - `compliant = all critical checks pass` (checks 1-4, 7 are critical; 5-6 are warnings)
   - `warning = "This advice may not be suitable for your profile"` if non-compliant

2. Tests (minimum 14):
   - Conservative investor + aggressive advice → FAIL (risk match)
   - "Guaranteed 20% returns" → FAIL (no guarantees)
   - "Invest your emergency fund" → FAIL (emergency fund)
   - Good advice with citations → PASS (all checks)
   - Sell recommendation without tax mention → WARN
   - Short-term trade for long-horizon investor → FAIL
   - Low evidence + specific claim → FAIL

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_principles.py -v
ruff check src/finroot/reasoning/principles.py
```

## Report
`work/reports/wave-5/03-principles.report.md`
