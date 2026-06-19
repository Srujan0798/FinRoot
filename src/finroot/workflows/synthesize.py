"""ResultSynthesizer — combines sub-agent tool_outputs into a structured Recommendation.

Contract: `.specify/specs/wave-4/contracts/graph.contract.md` § Result Synthesizer.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from finroot.schemas.enums import ConfidenceLevel
from finroot.schemas.recommendation import Citation, Recommendation
from finroot.schemas.state import AgentState

logger = logging.getLogger(__name__)

_NO_DATA_ANSWER = "I don't have enough data to answer. Please provide more details."


class ResultSynthesizer:
    """Combines all sub-agent tool_outputs into a structured Recommendation.

    Called as the ``synthesize`` node in the LangGraph pipeline.  Collects
    every tool output, extracts citations and risk flags, determines
    confidence, and builds a :class:`Recommendation`.
    """

    def synthesize(self, state: AgentState) -> Recommendation:
        """Build a :class:`Recommendation` from *state*'s tool_outputs.

        Args:
            state: The current :class:`AgentState` carrying all sub-agent
                   outputs.

        Returns:
            A fully populated :class:`Recommendation`.
        """
        outputs = list(state.tool_outputs)

        if not outputs:
            return Recommendation(
                summary=_NO_DATA_ANSWER,
                analysis="The pipeline produced no tool outputs.",
                confidence=ConfidenceLevel.LOW,
            )

        citations: list[Citation] = []
        risk_flags: list[str] = []
        errors: list[str] = []
        reasoning_steps: list[str] = []
        all_findings: list[str] = []

        for out in outputs:
            self._process_output(
                out, citations, risk_flags, errors, reasoning_steps, all_findings,
            )

        confidence = self._determine_confidence(outputs, errors)
        summary = self._build_summary(confidence, risk_flags, errors)
        analysis = self._build_analysis(all_findings, reasoning_steps)

        return Recommendation(
            summary=summary,
            analysis=analysis,
            risks=risk_flags,
            confidence=confidence,
            citations=citations,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _process_output(
        out: dict[str, Any],
        citations: list[Citation],
        risk_flags: list[str],
        errors: list[str],
        reasoning_steps: list[str],
        all_findings: list[str],
    ) -> None:
        """Extract all signals from a single tool-output entry."""
        tool_name: str = out.get("tool") or out.get("agent") or "unknown"

        if out.get("type") == "error":
            err_msg: str = str(out.get("error", "Unknown error"))
            errors.append(err_msg)
            reasoning_steps.append(f"{tool_name}: error — {err_msg}")
            return

        # --- Inline citations ---
        raw_citations = out.get("citations")
        if isinstance(raw_citations, list):
            for c in raw_citations:
                if isinstance(c, Citation):
                    if c not in citations:
                        citations.append(c)
                elif isinstance(c, dict):
                    _safe_add_citation(c, tool_name, citations)

        # --- Risk flags ---
        raw_risks = out.get("risk_flags")
        if isinstance(raw_risks, list):
            for r in raw_risks:
                if isinstance(r, str) and r not in risk_flags:
                    risk_flags.append(r)

        # --- Reasoning step ---
        output_type: str = out.get("type", "output")
        reasoning_steps.append(f"{tool_name}: produced {output_type}")

        # --- Finding text ---
        output_val = out.get("output")
        if output_val is not None:
            all_findings.append(f"[{tool_name}] {str(output_val)[:300]}")
        else:
            data_keys = [
                k
                for k in out
                if k
                not in (
                    "tool",
                    "agent",
                    "type",
                    "citations",
                    "risk_flags",
                    "input",
                    "output",
                    "error",
                )
            ]
            for k in data_keys:
                all_findings.append(f"[{tool_name}] {k}: {str(out[k])[:200]}")

    @staticmethod
    def _determine_confidence(
        outputs: list[dict[str, Any]],
        errors: list[str],
    ) -> ConfidenceLevel:
        """Determine :class:`ConfidenceLevel` per the task spec.

        * HIGH: ≥3 outputs with citations, no errors
        * MEDIUM: 1-2 outputs with citations, or some (but not all) errors
        * LOW: 0 outputs with citations, or all outputs are errors
        """
        if not outputs:
            return ConfidenceLevel.LOW

        outputs_with_citations = sum(1 for o in outputs if o.get("citations"))
        n_errors = len(errors)
        error_free = n_errors == 0
        all_errors = all(o.get("type") == "error" for o in outputs)

        if outputs_with_citations >= 3 and error_free:
            return ConfidenceLevel.HIGH
        if outputs_with_citations == 0 or all_errors:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.MEDIUM

    @staticmethod
    def _build_summary(
        confidence: ConfidenceLevel,
        risk_flags: list[str],
        errors: list[str],
    ) -> str:
        """Build a one-line summary."""
        parts = [f"Confidence: {confidence.value}"]
        if risk_flags:
            parts.append(f"Risk flags: {'; '.join(risk_flags)}")
        if errors:
            parts.append(f"Errors: {len(errors)}")
        return " | ".join(parts)

    @staticmethod
    def _build_analysis(
        all_findings: list[str],
        reasoning_steps: list[str],
    ) -> str:
        """Build a detailed analysis string from findings and reasoning steps."""
        lines = ["### Reasoning Process"]
        for step in reasoning_steps:
            lines.append(f"- {step}")

        if all_findings:
            lines.append("\n### Findings")
            for finding in all_findings:
                lines.append(f"- {finding}")

        return "\n".join(lines)


def _safe_add_citation(
    raw: dict[str, Any],
    default_source: str,
    dest: list[Citation],
) -> None:
    """Best-effort append a :class:`Citation` from a partial dict."""
    try:
        # If retrieved_at is missing, use current time
        ts = raw.get("retrieved_at")
        if ts is None:
            ts = datetime.now(UTC)
        dest.append(
            Citation(
                source=raw.get("source", default_source),
                detail=raw.get("detail", ""),
                value=str(raw["value"]) if "value" in raw else None,
                retrieved_at=ts,
            )
        )
    except Exception:
        logger.warning("Skipping malformed citation dict: %s", raw)


__all__ = ["ResultSynthesizer"]
