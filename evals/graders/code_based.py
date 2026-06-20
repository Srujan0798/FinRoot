"""Deterministic code-based grader for the FRB (Wave-6).

Scores an ``AgentState`` against a task spec from
``data/gold/frb_questions.json`` using hard, testable checks:

* **must_mention** — fraction of required keywords present in the answer text
  (case-insensitive substring match).
* **must_not** — if any red-flag phrase is present, the answer FAILS
  immediately (the "no rubber-stamp" gate; catches "guaranteed returns",
  "you will definitely", etc.).
* **citations** — count of ``state.final.citations`` (falling back to
  ``state.tool_outputs``) must meet ``min_citations``.
* **numeric** — if ``expected.numeric_answer`` is set, extract a numeric value
  from the answer and check it against ``expected.numeric_tolerance``.
* **confidence** — if ``expected.expected_confidence`` is set, compare to the
  agent's confidence label.

The final score is a weighted average of the soft axes, with the hard criteria
above applied as vetoes. The contract guarantees ``passed = (no hard fail)
AND score >= 0.6``.

Contract (frozen in ``.specify/specs/wave-6/contracts/evals.contract.md``)::

    class GradeResult(BaseModel):
        task_id: str
        passed: bool
        score: float            # 0.0-1.0
        breakdown: dict[str, Any]
        grader: str             # "code" | "llm_judge" | "human"

    def grade_code(task: dict, state: AgentState) -> GradeResult: ...
"""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from finroot.schemas.state import AgentState

# ---------------------------------------------------------------------------
# Regex patterns (compiled once)
# ---------------------------------------------------------------------------

# Numeric token — accepts currency prefix and thousands separators.
# Groups: the raw number string (commas preserved, may be "1,00,000" or "1.5").
_NUM_TOKEN_RE = re.compile(
    r"(?:[₹]|Rs\.?|INR|USD|\$|€|£)\s*"
    r"(\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
)
# Plain number (no currency prefix) — used as fallback.
_PLAIN_NUM_RE = re.compile(r"\b(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\b")

# ---------------------------------------------------------------------------
# Pydantic model (contract §1)
# ---------------------------------------------------------------------------


class GradeResult(BaseModel):
    """Result of grading one ``AgentState`` against one FRB task.

    All graders in ``evals/graders/`` return this shape so the harness can
    aggregate uniformly (see ``evals.contract.md`` § Grader interface).
    """

    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1, description="FRB task id (e.g. 'frb-001').")
    passed: bool = Field(description="True iff the answer meets all hard + soft criteria.")
    score: float = Field(ge=0.0, le=1.0, description="0.0-1.0 weighted score.")
    breakdown: dict[str, Any] = Field(
        default_factory=dict,
        description="Per-criterion detail (must_mention, must_not, citations, numeric, ...).",
    )
    grader: str = Field(
        default="code",
        description='One of "code", "llm_judge", "human".',
    )


# ---------------------------------------------------------------------------
# Scoring weights (sum to 1.0; cited in breakdown["weights"])
# ---------------------------------------------------------------------------

# Weights chosen so that failing any single soft criterion pulls the score
# below the 0.6 pass threshold for a non-trivial answer:
#   - citation weight is the highest single soft weight (0.40)
#   - missing keywords alone (0.30) still leaves 0.70 — must combine with
#     another miss to fail a real answer
#   - missing citations alone drops a perfect answer from 1.0 to 0.60, on the
#     threshold boundary; combined with a short analysis it fails clearly.
WEIGHTS: dict[str, float] = {
    "must_mention": 0.30,
    "citation_count": 0.40,
    "confidence": 0.10,
    "actionability_proxy": 0.15,
    "length_proxy": 0.05,
}

# Citation count is also a HARD criterion when min_citations > 0 — this is
# the structural enforcement of the anti-pattern: "answer with zero citations
# on a numeric claim must FAIL" (contract § acceptance anti-patterns).

# Pass threshold for the weighted score.
SCORE_THRESHOLD: float = 0.6


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_answer_text(state: AgentState) -> str:
    """Build the searchable text from a state's final recommendation.

    Concatenates summary, analysis, risks, and actions (lowercased at the
    call site) so keyword searches catch content anywhere in the answer.
    """
    if state.final is None:
        return ""
    parts: list[str] = [
        state.final.summary,
        state.final.analysis,
        *state.final.risks,
        *state.final.actions,
    ]
    return " \n ".join(p for p in parts if p)


def _extract_numeric_candidates(text: str) -> list[float]:
    """Return numeric candidates from *text*, currency-tagged ones first.

    Parses both money-style numbers (``₹10,400``, ``Rs. 10400``) and plain
    numbers. Returns them in document order; the caller picks the best match
    against ``expected.numeric_answer``.
    """
    currency: list[float] = []
    plain: list[float] = []
    for m in _NUM_TOKEN_RE.finditer(text):
        raw = m.group(1).replace(",", "")
        try:
            currency.append(float(raw))
        except ValueError:
            continue
    for m in _PLAIN_NUM_RE.finditer(text):
        raw = m.group(1).replace(",", "")
        try:
            plain.append(float(raw))
        except ValueError:
            continue
    return currency + plain


def _citation_count(state: AgentState) -> int:
    """Count evidence items: prefer final citations, fall back to tool outputs."""
    if state.final is not None and state.final.citations:
        return len(state.final.citations)
    return len(state.tool_outputs)


def _has_must_not_hit(text_lower: str, must_not: list[str]) -> tuple[bool, str | None]:
    """Return ``(hit, phrase)``. *phrase* is the first red-flag found, if any."""
    for phrase in must_not:
        if phrase and phrase.lower() in text_lower:
            return True, phrase
    return False, None


# ---------------------------------------------------------------------------
# Public API (contract §1)
# ---------------------------------------------------------------------------


def grade_code(task: dict, state: AgentState) -> GradeResult:
    """Deterministic grade of one ``AgentState`` against one FRB task.

    Args:
        task: FRB task dict from ``data/gold/frb_questions.json``.
        state: AgentState to grade. ``state.final`` must be set; if not,
            raises ``ValueError`` (FM-11: nothing to grade).

    Returns:
        :class:`GradeResult` with ``passed``, weighted ``score`` (0.0-1.0),
        and a ``breakdown`` dict covering every criterion.

    Raises:
        ValueError: If ``state.final`` is None.
    """
    if state.final is None:
        raise ValueError(
            "grade_code: state.final is None — nothing to grade "
            "(FM-11: fail loud, never invent a recommendation)."
        )

    expected = task.get("expected", {}) or {}
    must_mention: list[str] = list(expected.get("must_mention") or [])
    must_not: list[str] = list(expected.get("must_not") or [])
    min_citations: int = int(expected.get("min_citations") or 0)
    expected_confidence: str | None = expected.get("expected_confidence")
    expected_numeric: float | None = expected.get("numeric_answer")
    expected_numeric_tol: float = float(expected.get("numeric_tolerance") or 0.0)

    text = _extract_answer_text(state)
    text_lower = text.lower()

    # ----- must_not (HARD FAIL) --------------------------------------------
    must_not_hit, must_not_phrase = _has_must_not_hit(text_lower, must_not)
    must_not_passed = not must_not_hit

    # ----- must_mention ----------------------------------------------------
    keywords_found: list[str] = []
    keywords_missing: list[str] = []
    for kw in must_mention:
        if kw and kw.lower() in text_lower:
            keywords_found.append(kw)
        else:
            keywords_missing.append(kw)
    mention_ratio = (
        len(keywords_found) / len(must_mention) if must_mention else 1.0
    )

    # ----- citations (HARD FAIL when min_citations > 0) -------------------
    citation_count = _citation_count(state)
    citations_passed = citation_count >= min_citations if min_citations > 0 else True

    # ----- numeric (HARD FAIL when expected) -------------------------------
    numeric_passed = True
    numeric_extracted: float | None = None
    numeric_diff: float | None = None
    if expected_numeric is not None:
        candidates = _extract_numeric_candidates(text)
        if not candidates:
            numeric_passed = False
        else:
            # Pick the candidate closest to the expected value. This is a
            # deterministic, audit-friendly choice — no LLM, no judgement.
            best = min(candidates, key=lambda v: abs(v - float(expected_numeric)))
            numeric_extracted = best
            numeric_diff = round(abs(best - float(expected_numeric)), 6)
            numeric_passed = numeric_diff <= expected_numeric_tol

    # ----- confidence ------------------------------------------------------
    confidence_passed = True
    if expected_confidence is not None and state.final.confidence is not None:
        confidence_passed = state.final.confidence.value == expected_confidence

    # ----- weighted score --------------------------------------------------
    has_actions = bool(state.final.actions)
    long_enough = len(text) >= 100
    score = (
        WEIGHTS["must_mention"] * mention_ratio
        + WEIGHTS["citation_count"] * (1.0 if citations_passed else 0.0)
        + WEIGHTS["confidence"] * (1.0 if confidence_passed else 0.0)
        + WEIGHTS["actionability_proxy"] * (1.0 if has_actions else 0.0)
        + WEIGHTS["length_proxy"] * (1.0 if long_enough else 0.0)
    )
    score = round(min(max(score, 0.0), 1.0), 4)

    passed = (
        must_not_passed
        and citations_passed
        and numeric_passed
        and confidence_passed
        and score >= SCORE_THRESHOLD
    )

    breakdown: dict[str, Any] = {
        "must_mention": {
            "required": must_mention,
            "found": keywords_found,
            "missing": keywords_missing,
            "ratio": round(mention_ratio, 4),
        },
        "must_not": {
            "checked": must_not,
            "hit_phrase": must_not_phrase,
            "passed": must_not_passed,
        },
        "citations": {
            "count": citation_count,
            "min_required": min_citations,
            "passed": citations_passed,
        },
        "numeric": {
            "expected": expected_numeric,
            "tolerance": expected_numeric_tol,
            "extracted": numeric_extracted,
            "diff": numeric_diff,
            "passed": numeric_passed,
        },
        "confidence": {
            "expected": expected_confidence,
            "actual": (
                state.final.confidence.value
                if state.final.confidence is not None
                else None
            ),
            "passed": confidence_passed,
        },
        "weights": dict(WEIGHTS),
        "threshold": SCORE_THRESHOLD,
    }

    return GradeResult(
        task_id=str(task.get("id", "")),
        passed=passed,
        score=score,
        breakdown=breakdown,
        grader="code",
    )


__all__ = ["GradeResult", "grade_code", "WEIGHTS", "SCORE_THRESHOLD"]
