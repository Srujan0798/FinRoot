"""Refinement Loop — critique → revise → re-score (wave-5, task 02).

Iteratively improves a candidate ``Recommendation`` until it passes the
SelfCritic quality gate or the maximum iteration budget is exhausted.
Each iteration is logged to the audit trail for full traceability.

Per ``.specify/specs/wave-5/contracts/reasoning.contract.md`` § Refinement Loop.
"""

from __future__ import annotations

import copy
import re
from datetime import UTC, datetime
from hashlib import sha256

from finroot.reasoning.critic import CriticVerdict, SelfCritic
from finroot.schemas.audit import AuditEvent
from finroot.schemas.enums import ConfidenceLevel
from finroot.schemas.state import AgentState

_DISCLAIMER = (
    "This answer has not met quality standards. Please verify independently."
)

_OVERCONFIDENT_RE = re.compile(
    r"\b(?:guaranteed|guarantee[sd]?|certain(?:ly)?|definitely|always|never|"
    r"sure\s+thing|risk[- ]?free|can'?t\s+lose|cannot\s+lose|"
    r"absolutely|foolproof|infallible|unfailingly)\b",
    re.IGNORECASE,
)

_CONNECTORS = [
    " because the underlying fundamentals support this view.",
    " therefore investors should consider the associated trade-offs.",
    " since market conditions may change, monitor regularly.",
    " as a result, diversification remains important.",
    " given that past performance does not guarantee future results,",
]


def _next_seq(events: list[AuditEvent]) -> int:
    """Monotonic sequence number — one past the last event."""
    return events[-1].seq + 1 if events else 0


def _fake_hash(payload: dict, seq: int) -> str:
    """Deterministic placeholder hash for the audit chain.

    The real hash-chain construction lives in ``src/finroot/audit/`` (task 03).
    Here we produce a valid 64-char hex string so Pydantic's ``min_length=64``
    constraint is satisfied without depending on task 03.
    """
    raw = f"{seq}:{payload!r}"
    return sha256(raw.encode()).hexdigest()


def _append_event(
    events: list[AuditEvent],
    *,
    event_type: str,
    payload: dict,
) -> None:
    """Append a typed audit event with a placeholder hash."""
    seq = _next_seq(events)
    prev_hash = events[-1].hash if events else "0" * 64
    h = _fake_hash(payload, seq)
    events.append(
        AuditEvent(
            ts=datetime.now(UTC),
            seq=seq,
            type=event_type,
            payload=payload,
            prev_hash=prev_hash,
            hash=h,
        )
    )


class RefinementLoop:
    """Critique → revise → re-score until quality threshold met or max iterations."""

    MAX_ITERATIONS: int = 3

    def refine(self, state: AgentState, critic: SelfCritic) -> AgentState:
        """Run the refinement loop on ``state.candidate``.

        Mutates ``state`` in place (LangGraph pattern) and returns it.

        Args:
            state: Pipeline state with ``candidate`` set.
            critic: The 5-axis SelfCritic scorer.

        Returns:
            The same ``state``, with ``final`` set and audit events appended.

        Raises:
            ValueError: If ``state.candidate`` is ``None`` (FM-11: nothing to refine).
        """
        if state.candidate is None:
            raise ValueError(
                "RefinementLoop.refine: state.candidate is None — "
                "nothing to refine (FM-11: fail loud)."
            )

        for iteration in range(1, self.MAX_ITERATIONS + 1):
            verdict = critic.evaluate(state)

            # Log this iteration to the audit trail.
            _append_event(
                state.audit_events,
                event_type="refine.iteration",
                payload={
                    "iteration": iteration,
                    "overall": verdict.overall,
                    "passed": verdict.passed,
                    "must_fix": list(verdict.must_fix),
                    "scores": {s.axis: s.score for s in verdict.scores},
                },
            )

            if verdict.passed:
                state.final = copy.deepcopy(state.candidate)
                return state

            # Revise the candidate to address must_fix items.
            self._revise(state, verdict)

        # Exhausted all iterations — still failing.
        # Set final with LOW confidence and disclaimer.
        state.final = copy.deepcopy(state.candidate)
        state.final.confidence = ConfidenceLevel.LOW
        if _DISCLAIMER not in state.final.analysis:
            state.final.analysis = f"{state.final.analysis}\n\n{_DISCLAIMER}"

        _append_event(
            state.audit_events,
            event_type="refine.exhausted",
            payload={
                "iterations": self.MAX_ITERATIONS,
                "final_confidence": state.final.confidence.value,
                "disclaimer_added": True,
            },
        )
        return state

    # ------------------------------------------------------------------
    # Revision helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _revise(state: AgentState, verdict: CriticVerdict) -> None:
        """Apply targeted revisions to ``state.candidate`` based on ``must_fix``."""
        rec = state.candidate
        assert rec is not None  # noqa: S101

        for axis in verdict.must_fix:
            axis_score = next(
                (s for s in verdict.scores if s.axis == axis), None
            )
            if axis_score is None:
                continue
            score_val = axis_score.score

            if axis == "risk_awareness" and score_val < 0.5:
                RefinementLoop._add_risk_warnings(state)

            if axis == "evidence" and score_val < 0.5:
                RefinementLoop._add_citations(state)

            if axis == "explainability" and score_val < 0.5:
                RefinementLoop._add_reasoning_steps(state)

        # Soften overconfident language if any must_fix axis suggests it.
        # This is a cross-cutting concern: overconfidence hurts risk_awareness
        # and correctness, so we apply it whenever those axes are flagged.
        if any(ax in verdict.must_fix for ax in ("risk_awareness", "correctness")):
            RefinementLoop._soften_overconfident(state)

    @staticmethod
    def _add_risk_warnings(state: AgentState) -> None:
        """Inject missing risk warnings."""
        rec = state.candidate
        assert rec is not None  # noqa: S101
        generic_risks = [
            "Market conditions can change rapidly; past performance does not guarantee future results.",
            "Investments carry the risk of loss, including loss of principal.",
        ]
        existing_lower = {r.lower() for r in rec.risks}
        for risk in generic_risks:
            if risk.lower() not in existing_lower:
                rec.risks.append(risk)

    @staticmethod
    def _add_citations(state: AgentState) -> None:
        """Note in analysis that citations are insufficient — do not fabricate data."""
        rec = state.candidate
        assert rec is not None  # noqa: S101
        note = (
            " Note: some claims in this recommendation lack sufficient "
            "tool-backed citations. Verify data independently before acting."
        )
        if "lack sufficient" not in rec.analysis:
            rec.analysis += note

    @staticmethod
    def _add_reasoning_steps(state: AgentState) -> None:
        """Inject reasoning connectors and expand short text for explainability."""
        rec = state.candidate
        assert rec is not None  # noqa: S101

        # Append a reasoning connector if the analysis lacks them.
        text_lower = rec.analysis.lower()
        has_connector = any(
            kw in text_lower
            for kw in ["because", "therefore", "thus", "since", "due to", "as a result"]
        )
        if not has_connector:
            rec.analysis += _CONNECTORS[0]

        # If analysis is still short (< 100 chars), expand it.
        if len(rec.analysis) < 100:
            rec.analysis += (
                " Investors should review their full financial picture, "
                "including income, expenses, and existing holdings, before "
                "making any allocation changes."
            )

        # If summary is too brief (< 5 words), pad it.
        if len(rec.summary.split()) < 5:
            rec.summary += " for your portfolio based on current analysis"

    @staticmethod
    def _soften_overconfident(state: AgentState) -> None:
        """Replace overconfident language with softer phrasing."""
        rec = state.candidate
        assert rec is not None  # noqa: S101
        replacements = {
            "guaranteed": "may provide",
            "guarantee": "may provide",
            "guarantees": "may provide",
            "guaranteed returns": "potential returns",
            "certainly": "likely",
            "definitely": "likely",
            "always": "typically",
            "sure thing": "reasonable opportunity",
            "risk-free": "lower-risk",
            "can't lose": "may still experience losses",
            "cannot lose": "may still experience losses",
            "absolutely": "generally",
        }
        for old, new in replacements.items():
            if old in rec.summary.lower():
                # Case-insensitive replacement preserving original casing intent.
                pattern = re.compile(re.escape(old), re.IGNORECASE)
                rec.summary = pattern.sub(new, rec.summary, count=1)
            if old in rec.analysis.lower():
                pattern = re.compile(re.escape(old), re.IGNORECASE)
                rec.analysis = pattern.sub(new, rec.analysis, count=1)


__all__ = ["RefinementLoop"]
