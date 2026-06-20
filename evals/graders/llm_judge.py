"""LLM-judge grader for the FRB (5-axis reasoning quality rubric).

The judge prompt asks for five orthogonal axis scores, each on a 0.0-1.0
scale: ``correctness · risk_awareness · actionability · explainability ·
evidence_grounding``. The LLM response is parsed deterministically (regex
on ``"<axis>: <score>"`` lines). If parsing fails for an axis — e.g. when
the offline ``MockProvider`` returns one of its canned, non-rubric
responses — a content-based heuristic fallback produces a stable score so
the grader remains reproducible and ``MockProvider`` is test-stable.

The five axes are sourced from the self-critic where possible (so a future
wave can wire the LLM judge into the critic without rewriting it); if the
critic cannot be imported, this grader degrades gracefully to its own
5-tuple of axis names.

Contract (frozen in ``.specify/specs/wave-6/contracts/evals.contract.md``)::

    def grade_llm(task: dict, state: AgentState, judge_llm) -> GradeResult
"""
from __future__ import annotations

import re
from typing import Any, Protocol

from evals.graders.code_based import GradeResult

from finroot.schemas.state import AgentState

# ---------------------------------------------------------------------------
# Axis registry — reuse the critic's if importable, else our own.
# ---------------------------------------------------------------------------

# Canonical 5-axis rubric (also used as the default if the critic import
# is unavailable). These names match the 5-axis template in
# ``human_review_template.md`` and the critic's axis tuple.
DEFAULT_JUDGE_AXES: tuple[str, ...] = (
    "correctness",
    "risk_awareness",
    "actionability",
    "explainability",
    "evidence_grounding",
)


def _resolve_axes() -> tuple[str, ...]:
    """Return the critic's axis tuple if importable, else the default.

    The critic's ``AXES`` is a 5-tuple of strings; we accept it as-is to
    avoid drift. If the import fails for any reason (missing dep, refactor),
    fall back to ``DEFAULT_JUDGE_AXES`` so the grader still runs.
    """
    try:
        from finroot.reasoning.critic import AXES as critic_axes  # type: ignore
    except Exception:  # pragma: no cover — degrade gracefully
        return DEFAULT_JUDGE_AXES
    if (
        isinstance(critic_axes, tuple)
        and len(critic_axes) == 5
        and all(isinstance(a, str) and a for a in critic_axes)
    ):
        # Map critic's shorter "evidence" axis to the LLM-judge's
        # "evidence_grounding" naming (the rubric exposes a richer name).
        mapped = tuple("evidence_grounding" if a == "evidence" else a for a in critic_axes)
        return mapped
    return DEFAULT_JUDGE_AXES


JUDGE_AXES: tuple[str, ...] = _resolve_axes()


# ---------------------------------------------------------------------------
# Regex patterns (compiled once)
# ---------------------------------------------------------------------------

# Parses "<axis>: <score>" or "<axis> = <score>" or markdown list "- <axis>: <score>".
# Captures the axis name and the score (0.0-1.0 float).
_AXIS_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:\*\*)?"
    r"(?P<axis>correctness|risk_awareness|actionability|explainability|evidence|evidence_grounding)"
    r"(?:\*\*)?\s*[:\-=]\s*"
    r"(?P<score>\d+(?:\.\d+)?)",
    re.IGNORECASE | re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Protocol — a structural duck type for the judge LLM.
# ---------------------------------------------------------------------------


class _JudgeLLM(Protocol):
    """Minimal duck-type for the judge LLM. Any ``LLMProvider`` satisfies it."""

    name: str

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> Any: ...


# ---------------------------------------------------------------------------
# Prompt + parsing
# ---------------------------------------------------------------------------


def build_judge_prompt(task: dict, state: AgentState) -> str:
    """Build the 5-axis rubric prompt sent to the judge LLM.

    Exposed (not just used internally) so tests and the report generator
    can inspect the rubric without invoking the judge.

    Args:
        task: FRB task dict from ``data/gold/frb_questions.json``.
        state: AgentState to grade. If ``state.final`` is None, a sentinel
            placeholder is substituted so the LLM can still judge (the
            caller decides whether to raise).
    """
    query = str(task.get("query", ""))
    domain = str(task.get("domain", ""))
    difficulty = str(task.get("difficulty", ""))
    expected = task.get("expected", {}) or {}
    must_mention = expected.get("must_mention") or []
    must_not = expected.get("must_not") or []

    if state.final is None:
        answer = "(no answer — state.final is None)"
    else:
        f = state.final
        answer = (
            f"Summary: {f.summary}\n"
            f"Analysis: {f.analysis}\n"
            f"Risks: {'; '.join(f.risks) if f.risks else '(none)'}\n"
            f"Actions: {'; '.join(f.actions) if f.actions else '(none)'}\n"
            f"Confidence: {f.confidence.value if f.confidence else 'unset'}\n"
            f"Citations: {len(f.citations)} cited"
        )

    axes_lines = "\n".join(f"- {a}: <score 0.0-1.0>" for a in JUDGE_AXES)

    return (
        "You are a strict reasoning-quality judge for an AI financial agent. "
        "Score the agent's answer on five axes, each from 0.0 to 1.0. "
        "Be strict: empty answers, uncited numeric claims, guarantees, and "
        "'you will definitely' language must score low.\n\n"
        "## Task\n"
        f"Domain: {domain}\n"
        f"Difficulty: {difficulty}\n"
        f"Query: {query}\n\n"
        "## Expected behavior\n"
        f"Must mention: {must_mention}\n"
        f"Must NOT contain: {must_not}\n\n"
        "## Agent answer\n"
        f"{answer}\n\n"
        "## Scoring\n"
        f"For each axis below, output one number 0.0-1.0 with a one-line rationale.\n"
        f"{axes_lines}\n\n"
        "Format each line as `<axis>: <score>` for parsing. "
        "Order does not matter. Output ONLY the axis lines and rationale."
    )


def _parse_axis_scores(text: str) -> dict[str, float]:
    """Parse the LLM response for axis: score lines.

    Missing axes default to 0.0. The critic's ``evidence`` axis is mapped
    to ``evidence_grounding`` so the contract name wins.
    """
    scores: dict[str, float] = dict.fromkeys(JUDGE_AXES, 0.0)
    for m in _AXIS_RE.finditer(text):
        raw_axis = m.group("axis").lower()
        normalized = "evidence_grounding" if raw_axis == "evidence" else raw_axis
        if normalized not in scores:
            continue
        try:
            raw = float(m.group("score"))
        except ValueError:
            continue
        scores[normalized] = max(0.0, min(1.0, raw))
    return scores


def _heuristic_axis_scores(state: AgentState) -> dict[str, float]:
    """Content-based fallback for when the LLM response can't be parsed.

    Deterministic — given the same ``state``, returns the same scores.
    Used automatically by ``grade_llm`` when the regex misses an axis; this
    is also what ``MockProvider`` (which returns canned prose, not a rubric)
    triggers in practice.
    """
    if state.final is None:
        return dict.fromkeys(JUDGE_AXES, 0.0)
    text_lower = f"{state.final.summary} {state.final.analysis}".lower()
    has_actions = bool(state.final.actions)
    has_risks = bool(state.final.risks)
    has_citations = bool(state.final.citations)
    substance_keywords = ("risk", "tax", "return", "allocation", "diversif", "rate")
    keyword_hits = sum(1 for kw in substance_keywords if kw in text_lower)
    length = len(text_lower)
    return {
        "correctness": round(min(1.0, 0.3 + 0.15 * keyword_hits), 4),
        "risk_awareness": 0.8 if has_risks else 0.2,
        "actionability": 0.8 if has_actions else 0.2,
        "explainability": round(min(1.0, length / 400.0), 4),
        "evidence_grounding": 0.8 if has_citations else 0.1,
    }


# ---------------------------------------------------------------------------
# Public API (contract §1)
# ---------------------------------------------------------------------------


def grade_llm(task: dict, state: AgentState, judge_llm: _JudgeLLM) -> GradeResult:
    """LLM-judge grade of one ``AgentState`` against one FRB task.

    Args:
        task: FRB task dict (from ``data/gold/frb_questions.json``).
        state: AgentState to grade. ``state.final`` must be set; raises
            ``ValueError`` otherwise (FM-11).
        judge_llm: Any object with ``.complete(prompt) -> LLMResult`` —
            typically an ``LLMProvider`` (``MockProvider``, ``OllamaProvider``,
            etc.). Must NOT be None.

    Returns:
        :class:`GradeResult` with the 5-axis scores as ``breakdown["axes"]``
        and the mean as ``score``. ``breakdown["score_source"]`` is either
        ``"judge_llm"`` (parsed from the response) or ``"heuristic_fallback"``
        (parsed nothing — used the deterministic fallback).
    """
    if state.final is None:
        raise ValueError(
            "grade_llm: state.final is None — nothing to judge (FM-11)."
        )
    if judge_llm is None:
        raise ValueError("grade_llm: judge_llm is None — provide a provider.")

    prompt = build_judge_prompt(task, state)
    result = judge_llm.complete(prompt)
    response_text = getattr(result, "text", str(result))

    parsed = _parse_axis_scores(response_text)
    parsed_any = any(parsed[a] > 0.0 for a in JUDGE_AXES)

    if parsed_any:
        scores = parsed
        score_source = "judge_llm"
    else:
        scores = _heuristic_axis_scores(state)
        score_source = "heuristic_fallback"

    overall = round(sum(scores[a] for a in JUDGE_AXES) / len(JUDGE_AXES), 4)
    passed = overall >= 0.6

    breakdown: dict[str, Any] = {
        "axes": scores,
        "axes_order": list(JUDGE_AXES),
        "mean": overall,
        "score_source": score_source,
        "judge_response_excerpt": response_text[:240],
    }

    return GradeResult(
        task_id=str(task.get("id", "")),
        passed=passed,
        score=overall,
        breakdown=breakdown,
        grader="llm_judge",
    )


__all__ = [
    "DEFAULT_JUDGE_AXES",
    "JUDGE_AXES",
    "build_judge_prompt",
    "grade_llm",
    "_parse_axis_scores",
    "_heuristic_axis_scores",
]
