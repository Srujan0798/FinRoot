"""Self-Critic — 5-axis reasoning quality scorer (wave-5, task 01).

The gate that catches bad advice before it reaches the user. Evaluates a
candidate ``Recommendation`` along five orthogonal axes (correctness ·
risk-awareness · actionability · explainability · evidence), produces a
weighted overall score, and flags axes that must be fixed before the
recommendation ships.

This is a deterministic heuristic scorer — no LLM dependency — so it works
in offline / mock mode (the sovereign default) and can be unit-tested without
external services. The language patterns were chosen to be:

* conservative (false-positive-free at the ``THRESHOLD`` boundary),
* language-agnostic enough to catch English templates and most LLM outputs,
* auditable (every score carries a ``rationale`` and ``issues`` trace).

Per ``.specify/specs/wave-5/contracts/reasoning.contract.md`` § Self-Critic.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field

from finroot.schemas.recommendation import Recommendation
from finroot.schemas.state import AgentState

# ---------------------------------------------------------------------------
# Axis registry (contract §1) — canonical order used everywhere
# ---------------------------------------------------------------------------

AXES: tuple[str, ...] = (
    "correctness",
    "risk_awareness",
    "actionability",
    "explainability",
    "evidence",
)


# ---------------------------------------------------------------------------
# Pydantic models (contract §1)
# ---------------------------------------------------------------------------


class CriticScore(BaseModel):
    """A single axis score: 0.0 (broken) → 1.0 (excellent)."""

    model_config = ConfigDict(extra="forbid")

    axis: str = Field(min_length=1, description="One of the 5 critic axes.")
    score: float = Field(ge=0.0, le=1.0, description="0.0-1.0 axis score.")
    rationale: str = Field(min_length=1, description="Why this score.")
    issues: list[str] = Field(
        default_factory=list,
        description="Concrete problems that lowered the score.",
    )


class CriticVerdict(BaseModel):
    """The full 5-axis evaluation of a candidate recommendation."""

    model_config = ConfigDict(extra="forbid")

    scores: list[CriticScore] = Field(
        ...,
        min_length=1,
        description="One CriticScore per axis.",
    )
    overall: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted average across axes (WEIGHTS sum to 1.0).",
    )
    passed: bool = Field(..., description="True iff overall >= THRESHOLD.")
    summary: str = Field(..., min_length=1, description="Human-readable verdict.")
    must_fix: list[str] = Field(
        default_factory=list,
        description=(
            "Names of axes whose score is below MUST_FIX_THRESHOLD. The "
            "detailed issues for each axis live in CriticScore.issues."
        ),
    )


# ---------------------------------------------------------------------------
# Regex patterns (compiled once)
# ---------------------------------------------------------------------------

# Numbers in text: integers and decimals (no leading sign). Percent / currency
# characters are stripped separately — we want the raw numeric token.
_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?")

# Epistemic uncertainty phrases — honesty signal, but the agent must not still
# give a tip after expressing uncertainty.
_UNCERTAINTY_RE = re.compile(
    r"\b(?:i\s+don'?t\s+know|i'?m\s+not\s+sure|uncertain|no\s+idea|"
    r"can'?t\s+say|hard\s+to\s+say|don'?t\s+have\s+enough)\b",
    re.IGNORECASE,
)

# Risk-aware language (both standalone words and phrases).
_RISK_KEYWORD_RE = re.compile(
    r"\b(?:risk|risks|risk\s+of|warn|caution|downside|downside[s]?|"
    r"volatile|volatility|could\s+lose|might\s+lose|may\s+lose|"
    r"loss|losses|exposure|hedge|drawdown|stress[- ]?test|scenario|"
    r"worst[- ]?case|tail[- ]?risk|liquidity|credit\s+risk|market\s+risk|"
    r"underwater|haircut|inflation|recession|bear\s+market)\b",
    re.IGNORECASE,
)

# Forbidden aggressive patterns — these signal irresponsible advice
# regardless of other mitigating language. Plural variants included.
_FORBIDDEN_RISK_RE = re.compile(
    r"\b(?:penny\s+stocks?|all[- ]?in|guarantee[ds]?|"
    r"can'?t\s+lose|cannot\s+lose|risk[- ]?free|sure\s+thing|"
    r"moonshot|yolo|meme\s+stocks?)\b",
    re.IGNORECASE,
)

# Action verbs (specific, executable advice).
_ACTION_VERB_RE = re.compile(
    r"\b(?:buy|sell|hold|rebalance|allocate|invest|divest|reduce|increase|"
    r"diversif|hedge|set\s+aside|open|close|deposit|withdraw|roll|review|"
    r"monitor|dollar[- ]?cost\s+average|dca|trim|top\s*up|exit)\b",
    re.IGNORECASE,
)

# Temporal hints (when to act).
_TEMPORAL_HINT_RE = re.compile(
    r"\b(?:today|tomorrow|next\s+(?:week|month|quarter|year)|"
    r"in\s+\d+\s+(?:days?|weeks?|months?|years?)|"
    r"by\s+(?:end\s+of\s+)?(?:Q[1-4]|january|february|march|april|may|june|"
    r"july|august|september|october|november|december)|"
    r"within\s+\d+|monthly|quarterly|annually|weekly|daily|yearly|"
    r"over\s+the\s+next)\b",
    re.IGNORECASE,
)

# Chain-of-thought markers — show your work.
_REASONING_CONNECTOR_RE = re.compile(
    r"\b(?:because|therefore|thus|hence|since|due\s+to|as\s+a\s+result|"
    r"consequently|so\s+that|given\s+that|considering|based\s+on|"
    r"according\s+to|in\s+light\s+of|reasoning|analysis\s+shows|"
    r"this\s+(?:means|implies|suggests)|which\s+(?:means|implies))\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# SelfCritic
# ---------------------------------------------------------------------------


class SelfCritic:
    """5-axis reasoning quality scorer. The gate that prevents bad advice.

    The scoring rules are deterministic and rule-based — they do NOT call an
    LLM. This makes the scorer reproducible in tests and offline-judging
    scenarios. A future wave may layer an LLM "second opinion" on top of
    this heuristic baseline without changing the contract.
    """

    THRESHOLD: float = 0.6
    WEIGHTS: dict[str, float] = {
        "correctness": 0.30,
        "risk_awareness": 0.25,
        "actionability": 0.20,
        "explainability": 0.15,
        "evidence": 0.10,
    }
    MUST_FIX_THRESHOLD: float = 0.5

    # ------------------------------------------------------------------
    # Public API (contract §1)
    # ------------------------------------------------------------------

    def evaluate(self, state: AgentState) -> CriticVerdict:
        """Score the candidate recommendation in `state` along all 5 axes.

        Args:
            state: Current ``AgentState``. Reads ``state.candidate`` (falls
                back to ``state.final``) and ``state.tool_outputs``.

        Returns:
            ``CriticVerdict`` with per-axis scores, weighted overall, pass/fail,
            human-readable summary, and ``must_fix`` list of axis names.

        Raises:
            ValueError: If neither ``state.candidate`` nor ``state.final`` is
                set (FM-11: nothing to evaluate, never invent a recommendation).
        """
        rec = state.candidate or state.final
        if rec is None:
            raise ValueError(
                "SelfCritic.evaluate: no candidate or final recommendation in "
                "state. Nothing to evaluate (FM-11: fail loud)."
            )

        scores = self._score_axes(state, rec)
        overall = self._compute_overall(scores)
        passed = overall >= self.THRESHOLD
        must_fix = [s.axis for s in scores if s.score < self.MUST_FIX_THRESHOLD]
        summary = self._build_summary(scores, overall, passed, must_fix)

        return CriticVerdict(
            scores=scores,
            overall=round(overall, 4),
            passed=passed,
            summary=summary,
            must_fix=must_fix,
        )

    # ------------------------------------------------------------------
    # Axis scorers (public so refine.py and tests can call individually)
    # ------------------------------------------------------------------

    def score_correctness(
        self, state: AgentState, rec: Recommendation
    ) -> CriticScore:
        """Are numbers accurate? Do they match tool outputs?

        Public so ``RefinementLoop`` (task 02) can re-score a single axis
        after a candidate is revised, without re-running all 5 scorers.
        """
        return self._score_correctness(state, rec)

    def score_risk_awareness(
        self, state: AgentState, rec: Recommendation
    ) -> CriticScore:
        """Does the answer flag risks? Does it warn about downsides?"""
        return self._score_risk_awareness(rec)

    def score_actionability(
        self, state: AgentState, rec: Recommendation
    ) -> CriticScore:
        """Is the advice specific enough to act on (what / when / how)?"""
        return self._score_actionability(rec)

    def score_explainability(
        self, state: AgentState, rec: Recommendation
    ) -> CriticScore:
        """Can the user follow the reasoning chain?"""
        return self._score_explainability(rec)

    def score_evidence(
        self, state: AgentState, rec: Recommendation
    ) -> CriticScore:
        """Is every claim backed by a tool output citation? Are sources named?"""
        return self._score_evidence(rec)

    # ------------------------------------------------------------------
    # Pipeline internals (test seams)
    # ------------------------------------------------------------------

    def _score_axes(self, state: AgentState, rec: Recommendation) -> list[CriticScore]:
        """Run all 5 axis scorers. Extracted so tests can monkeypatch."""
        return [
            self._score_correctness(state, rec),
            self._score_risk_awareness(rec),
            self._score_actionability(rec),
            self._score_explainability(rec),
            self._score_evidence(rec),
        ]

    def _compute_overall(self, scores: list[CriticScore]) -> float:
        """Weighted average across the 5 axes (weights sum to 1.0)."""
        return sum(self.WEIGHTS[s.axis] * s.score for s in scores)

    @staticmethod
    def _build_summary(
        scores: list[CriticScore],
        overall: float,
        passed: bool,
        must_fix: list[str],
    ) -> str:
        verdict_word = "passed" if passed else "failed"
        breakdown = ", ".join(f"{s.axis}={s.score:.2f}" for s in scores)
        summary = (
            f"SelfCritic {verdict_word} (overall={overall:.2f}, "
            f"threshold={SelfCritic.THRESHOLD}). Axes: {breakdown}."
        )
        if must_fix:
            summary += f" Must fix: {', '.join(must_fix)}."
        return summary

    # ------------------------------------------------------------------
    # Axis scorers (private implementations)
    # ------------------------------------------------------------------

    def _score_correctness(self, state: AgentState, rec: Recommendation) -> CriticScore:
        """Numbers in the answer must appear in tool_outputs (no hallucination).

        Scoring bands:
            * Epistemic uncertainty expressed → 0.2
            * No numeric claims → 0.8 (nothing to verify)
            * Numeric claims, no tool_outputs → 0.1
            * Numeric claims, partial match → 0.1 + 0.9 * ratio
            * Numeric claims, all match → 1.0
        """
        text = f"{rec.summary}\n{rec.analysis}"

        if _UNCERTAINTY_RE.search(text):
            return CriticScore(
                axis="correctness",
                score=0.2,
                rationale=(
                    "Answer expresses epistemic uncertainty; any subsequent "
                    "claims are unverified."
                ),
                issues=["contains uncertainty language (e.g. 'I don't know')"],
            )

        unique_numbers = set(_NUMBER_RE.findall(text))
        if not unique_numbers:
            return CriticScore(
                axis="correctness",
                score=0.8,
                rationale=(
                    "No numeric claims in analysis; nothing to verify "
                    "against tool outputs."
                ),
                issues=[],
            )

        if not state.tool_outputs:
            return CriticScore(
                axis="correctness",
                score=0.1,
                rationale=(
                    f"{len(unique_numbers)} numeric claim(s) made with no "
                    f"tool outputs to verify against."
                ),
                issues=[
                    f"Numeric claim {n} has no tool output to cite."
                    for n in sorted(unique_numbers)
                ],
            )

        corpus = " ".join(str(o) for o in state.tool_outputs)
        found = {n for n in unique_numbers if n in corpus}
        missing = sorted(n for n in unique_numbers if n not in found)
        ratio = len(found) / len(unique_numbers)
        score = round(0.1 + 0.9 * ratio, 4)

        return CriticScore(
            axis="correctness",
            score=score,
            rationale=(
                f"{len(found)}/{len(unique_numbers)} numeric claim(s) "
                f"verified against tool outputs."
            ),
            issues=[
                f"Numeric claim {n} not found in any tool output."
                for n in missing
            ],
        )

    def _score_risk_awareness(self, rec: Recommendation) -> CriticScore:
        """Are risks flagged? Is risk-warning language present? No forbidden patterns?

        Scoring is composed from positive signals (risks list, risk keywords),
        then capped by any forbidden aggressive pattern. "No forbidden pattern"
        alone does NOT award credit — only the active flagging of risks does.
        """
        text = f"{rec.summary}\n{rec.analysis}"
        issues: list[str] = []

        has_rich_risk_list = len(rec.risks) >= 2
        has_risk_list = len(rec.risks) >= 1
        has_risk_keywords = bool(_RISK_KEYWORD_RE.search(text))

        # Positive signals only.
        if has_rich_risk_list and has_risk_keywords:
            score = 1.0
        elif has_risk_list and has_risk_keywords:
            score = 0.8
            issues.append("only one risk item; consider more")
        elif has_risk_list:
            score = 0.5
            issues.append("risks listed but no risk-warning language in prose")
        elif has_risk_keywords:
            score = 0.3
            issues.append("risk language present but no structured risks list")
        else:
            score = 0.0
            issues.append("Risks list is empty; no downside warnings provided.")
            issues.append("No risk-warning language found in summary or analysis.")

        # Forbidden patterns are a ceiling — they indicate irresponsible
        # advice regardless of other signals. Exclude negated contexts
        # like "does not guarantee" or "no guarantee" which are risk warnings,
        # and quoted contexts like "'guaranteed' returns" which reference the concept.
        _NEGATION_RE = re.compile(
            r"\b(?:does\s+not|doesn't|don't|no|not|never)\s+\w*\s*guarantee|"
            r"""['"]guarantee[ds]?['"]|"""
            r"(?:not|never)\s+guarantee",
            re.IGNORECASE,
        )
        forbidden = _FORBIDDEN_RISK_RE.search(text)
        if forbidden is not None and not _NEGATION_RE.search(text):
            issues.append(
                f"Contains forbidden aggressive pattern: {forbidden.group()}."
            )
            score = min(score, 0.3)

        return CriticScore(
            axis="risk_awareness",
            score=min(round(score, 4), 1.0),
            rationale="Risk-awareness heuristic score.",
            issues=issues,
        )

    def _score_actionability(self, rec: Recommendation) -> CriticScore:
        """Specific what/when/how: populated actions, action verbs, temporal hints."""
        issues: list[str] = []
        score = 0.0

        if len(rec.actions) >= 2:
            score += 0.4
        elif len(rec.actions) == 1:
            score += 0.2
        else:
            issues.append("Actions list is empty; advice is not actionable.")

        actions_text = " ".join(rec.actions)
        if _ACTION_VERB_RE.search(actions_text):
            score += 0.3
        else:
            issues.append(
                "Actions lack clear action verbs (buy, sell, hold, etc.)."
            )

        if _TEMPORAL_HINT_RE.search(actions_text):
            score += 0.3
        else:
            issues.append("Actions lack temporal guidance (when to act).")

        return CriticScore(
            axis="actionability",
            score=min(round(score, 4), 1.0),
            rationale="Actionability heuristic score.",
            issues=issues,
        )

    def _score_explainability(self, rec: Recommendation) -> CriticScore:
        """Can the user follow the reasoning chain?"""
        text = rec.analysis
        issues: list[str] = []
        score = 0.0

        length = len(text)
        if length >= 200:
            score += 0.5
        elif length >= 100:
            score += 0.3
        elif length >= 50:
            score += 0.1
        else:
            issues.append(
                f"Analysis is too short ({length} chars); reasoning not visible."
            )

        if _REASONING_CONNECTOR_RE.search(text):
            score += 0.3
        else:
            issues.append(
                "No reasoning connectors (because, therefore, since, …) found."
            )

        summary_words = len(rec.summary.split())
        if summary_words >= 5:
            score += 0.2
        else:
            issues.append(f"Summary is too brief ({summary_words} words).")

        return CriticScore(
            axis="explainability",
            score=min(round(score, 4), 1.0),
            rationale="Explainability heuristic score.",
            issues=issues,
        )

    def _score_evidence(self, rec: Recommendation) -> CriticScore:
        """Are claims cited? Do citations carry values? Are sources diverse?"""
        citations = rec.citations
        issues: list[str] = []
        score = 0.0

        if len(citations) >= 2:
            score += 0.4
        elif len(citations) == 1:
            score += 0.2
        else:
            issues.append("Citations list is empty; no evidence attached.")

        with_value = [c for c in citations if c.value and c.value.strip()]
        if with_value:
            score += 0.3
        elif citations:
            issues.append("Citations lack a `value` field (the actual figure).")

        sources = {c.source for c in citations}
        if len(sources) >= 2:
            score += 0.3
        elif len(sources) == 1:
            score += 0.15
            issues.append(
                "Only one source cited; diverse sources strengthen evidence."
            )

        numbers = _NUMBER_RE.findall(rec.analysis)
        if numbers and not citations:
            issues.append(
                f"{len(numbers)} numeric claim(s) in analysis but zero citations."
            )
            score = min(score, 0.1)

        return CriticScore(
            axis="evidence",
            score=min(round(score, 4), 1.0),
            rationale="Evidence heuristic score.",
            issues=issues,
        )


__all__ = ["AXES", "CriticScore", "CriticVerdict", "SelfCritic"]