"""FRB graders — deterministic code-based + LLM-judge + human review template.

Three complementary graders that score an ``AgentState`` against a task spec
from ``data/gold/frb_questions.json``. None of them rubber-stamp — every
grader has explicit pass conditions and a numeric score that spreads.

* :func:`evals.graders.code_based.grade_code` — deterministic keyword, citation,
  numeric-tolerance, and confidence checks. The hard gate.
* :func:`evals.graders.llm_judge.grade_llm` — 5-axis reasoning quality rubric;
  LLM-powered but Mock-friendly (heuristic fallback for offline judging).
* :data:`evals.graders.human_review_template` — weekly reviewer form
  (§6.10 of FinRoot charter) used to calibrate the LLM-judge.

Contract (frozen in ``.specify/specs/wave-6/contracts/evals.contract.md``):

    class GradeResult(BaseModel):
        task_id: str
        passed: bool
        score: float            # 0.0-1.0
        breakdown: dict[str, Any]
        grader: str             # "code" | "llm_judge" | "human"
"""
from __future__ import annotations

from evals.graders.code_based import GradeResult, grade_code
from evals.graders.llm_judge import JUDGE_AXES, build_judge_prompt, grade_llm

__all__ = [
    "GradeResult",
    "grade_code",
    "grade_llm",
    "JUDGE_AXES",
    "build_judge_prompt",
]
