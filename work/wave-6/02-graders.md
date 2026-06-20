# Task wave-6/02 — Graders (code-based + LLM-judge + human template)

> Read `work/WORKER_PROMPT.md` then build. Depends on W6-01 (question bank).

## Objective
Three graders that score an AgentState answer against an FRB task: a deterministic code grader, an
LLM-judge (Mock-capable), and a human review template. They MUST catch bad answers (no rubber-stamp).

## Writes (ONLY these)
- `evals/graders/__init__.py`
- `evals/graders/code_based.py`
- `evals/graders/llm_judge.py`
- `evals/graders/human_review_template.md`
- `tests/unit/test_graders.py`

## Forbid
`data/gold/**`, `src/finroot/evaluation/**`, `scripts/run_evals.py` (other tasks).

## Contract
Read `.specify/specs/wave-6/contracts/evals.contract.md` § Grader interface + anti-patterns.
FRB task shape from `data/gold/frb_questions.json` (read it). `GradeResult` per contract.

## Steps
1. `code_based.py` — `grade_code(task, state) -> GradeResult`:
   - must_mention: fraction of required keywords present in `state.final.summary + rationale` (case-insensitive).
   - must_not: if any red-flag phrase present → `passed=False` immediately.
   - citations: count `state.final.citations` (or tool_outputs) ≥ `min_citations`.
   - numeric: if `expected.numeric_answer` set, extract the number from the answer and check within tolerance.
   - confidence: if set, compare `state.final.confidence` label.
   - Weighted score; `passed = score >= 0.6 AND no must_not hit AND numeric matches (if required)`.
2. `llm_judge.py` — `grade_llm(task, state, judge_llm) -> GradeResult`:
   - Builds a judge prompt (5-axis rubric) → calls `judge_llm.complete()` → parses a 0-1 score per axis.
   - MockProvider returns deterministic judgments → test-stable.
   - Reuses the critic's axes if `finroot.reasoning.critic` is importable (degrade gracefully).
3. `human_review_template.md` — a markdown form: task id, the 5 axes with 1-5 scales, free-text notes, pass/fail, reviewer + date.
4. `tests/unit/test_graders.py` (min 12):
   - code grader PASSES a good answer (has keywords, citations, no red flags)
   - code grader FAILS an answer with a must_not phrase ("guaranteed returns")
   - code grader FAILS zero-citation numeric claim
   - numeric match within tolerance; numeric mismatch fails
   - llm_judge deterministic in mock; returns GradeResult with breakdown
   - graders never rubber-stamp: a deliberately empty/garbage answer FAILS both

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_graders.py -v
ruff check evals/graders/
```

## Report
`work/reports/wave-6/02-graders.report.md`
