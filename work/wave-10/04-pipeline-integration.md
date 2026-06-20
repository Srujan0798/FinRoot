# Task wave-10/04 — Pipeline Integration Tests

> Read `work/WORKER_PROMPT.md` then build. Proves the full pipeline works end-to-end.

## Objective
Add integration tests that exercise the full pipeline from query → AgentState → Recommendation.
These tests verify the wiring between all components (agents, tools, memory, reasoning).

## Writes (ONLY these)
- `tests/integration/test_full_pipeline.py`
- `tests/integration/test_pipeline_tax.py`
- `tests/integration/test_pipeline_trap.py`

## Forbid
`evals/**`, `data/gold/**` (import only).

## Steps
1. `test_full_pipeline.py` (8+ tests):
   - answer() returns AgentState with final Recommendation
   - answer() includes tool_outputs
   - answer() includes audit_events
   - answer() includes plan
   - answer() includes twin_snapshot
   - answer() works with mock=True
   - answer() works with different intents
   - answer() produces valid Recommendation (Pydantic validation)
2. `test_pipeline_tax.py` (4+ tests):
   - Tax query produces numeric answer
   - Tax query cites tax rules
   - Tax query has correct breakdown
   - Tax query mentions LTCG/STCG
3. `test_pipeline_trap.py` (4+ tests):
   - Emergency fund trap triggers prudence refusal
   - Guaranteed returns trap has LOW confidence
   - Leverage trap has risk warning
   - All traps have must_fix items
4. Use `interface.core.answer()` for all tests.
5. Use `@pytest.mark.integration` marker.

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/integration/ -v -m integration
ruff check tests/integration/
```

## Report
`work/reports/wave-10/04-pipeline-integration.report.md`
