"""Explainability Assembly — human-readable reasoning trace (wave-5, task 05).

Builds the ``dict`` that the UI renders as the "reasoning trace" tab. Extracts
reasoning steps, citations, confidence labels, prudence checks, and risk
summaries from the ``AgentState``. This is purely a *projection* — it reads
existing state fields and never modifies them (idempotent).
"""

from __future__ import annotations

from typing import Any

from finroot.schemas.state import AgentState

# ---------------------------------------------------------------------------
# Label thresholds  (contract §5)
# ---------------------------------------------------------------------------

_HIGH_THRESHOLD: float = 0.7
_LOW_THRESHOLD: float = 0.4

_MAX_RISK_TOOL_OUTPUTS: int = 5


# ---------------------------------------------------------------------------
# ExplainabilityAssembly
# ---------------------------------------------------------------------------


class ExplainabilityAssembly:
    """Build the human-readable reasoning trace from state.

    The ``assemble()`` method reads from ``AgentState`` fields that have been
    populated by earlier pipeline nodes (tasks 01‑04) and returns a plain dict
    that is safe to JSON-serialize and display.
    """

    def assemble(self, state: AgentState) -> dict[str, Any]:
        """Project ``state`` into the explainability output shape.

        Args:
            state: The current agent state with audit events, tool outputs,
                critique, and verifier verdict already populated.

        Returns:
            A dict matching the contract shape in
            ``.specify/specs/wave-5/contracts/reasoning.contract.md`` § 5.
        """
        return {
            "reasoning_chain": self._build_reasoning_chain(state.audit_events),
            "risk_summary": self._build_risk_summary(state.tool_outputs),
            "confidence_breakdown": self._build_confidence_breakdown(state.critique),
            "citations": self._build_citations(state.tool_outputs),
            "principles_check": self._build_principles_check(state.verifier_verdict),
        }

    # ------------------------------------------------------------------
    # Reasoning chain from audit events
    # ------------------------------------------------------------------

    @staticmethod
    def _build_reasoning_chain(
        audit_events: list[Any],
    ) -> list[dict[str, Any]]:
        """Map ``AuditEvent`` entries to a step-by-step reasoning trace.

        Each event becomes one step with its sequence number, event type,
        a short result description derived from the payload, and the
        event type reused as the source label.
        """
        return [
            {
                "step": e.seq,
                "action": e.type,
                "result": str(e.payload) if e.payload else "",
                "source": e.type,
            }
            for e in audit_events
        ]

    # ------------------------------------------------------------------
    # Risk summary from tool outputs
    # ------------------------------------------------------------------

    @staticmethod
    def _build_risk_summary(tool_outputs: list[dict]) -> str:
        """Scan tool outputs for risk-related content and build a summary.

        Looks for tool outputs whose keys or string representation mention
        ``risk``. Returns a one-line summary or a default message when no
        risk content is found.
        """
        risk_items: list[str] = []
        for out in tool_outputs:
            text = str(out).lower()
            if "risk" in text:
                label = out.get("tool", out.get("name", str(out)))
                detail = str(out)[:200]
                risk_items.append(f"{label}: {detail}")

        if not risk_items:
            return "No risk-related data in tool outputs."

        return " | ".join(risk_items[:_MAX_RISK_TOOL_OUTPUTS])

    # ------------------------------------------------------------------
    # Confidence breakdown from critique dict
    # ------------------------------------------------------------------

    @staticmethod
    def _build_confidence_breakdown(
        critique: dict | None,
    ) -> dict[str, Any]:
        """Map the critic verdict to a confidence label and axis scores.

        Label mapping (contract §5):
            * overall >= 0.7 → HIGH
            * 0.4 <= overall < 0.7 → MEDIUM
            * overall < 0.4 → LOW

        When no critique is available the label defaults to ``not evaluated``.
        """
        if critique is None:
            return {"label": "not evaluated", "axes": {}}

        overall = critique.get("overall", 0.0)
        if overall >= _HIGH_THRESHOLD:
            label = "HIGH"
        elif overall >= _LOW_THRESHOLD:
            label = "MEDIUM"
        else:
            label = "LOW"

        axes = {}
        for score in critique.get("scores", []):
            axes[score["axis"]] = score["score"]

        return {"label": label, "axes": axes}

    # ------------------------------------------------------------------
    # Citation list from tool outputs
    # ------------------------------------------------------------------

    @staticmethod
    def _build_citations(tool_outputs: list[dict]) -> list[dict[str, Any]]:
        """Extract a flat citation list from tool outputs.

        Each tool output that has a ``tool`` (or ``name``) key produces one
        citation entry. The payload is included as the ``data`` value.
        """
        citations: list[dict[str, Any]] = []
        for out in tool_outputs:
            source = out.get("tool", out.get("name", "unknown_tool"))
            citations.append(
                {
                    "claim": out.get("detail", out.get("description", str(out))),
                    "source": source,
                    "data": out,
                }
            )
        return citations

    # ------------------------------------------------------------------
    # Prudence check from verifier verdict dict
    # ------------------------------------------------------------------

    @staticmethod
    def _build_principles_check(
        verifier_verdict: dict | None,
    ) -> dict[str, Any]:
        """Project ``PrudentialVerdict`` into the explainability shape.

        When the verifier has not run, returns a safe default with
        ``compliant: True`` and a ``not checked`` warning (contract §5
        edge case).
        """
        if verifier_verdict is None:
            return {"compliant": True, "warnings": ["not checked"]}

        raw_warning = verifier_verdict.get("warning")
        warnings: list[str] = []
        if raw_warning:
            warnings.append(raw_warning)
        if not warnings:
            warnings = ["No prudence warnings."]

        return {
            "compliant": verifier_verdict.get("compliant", True),
            "warnings": warnings,
        }


__all__ = ["ExplainabilityAssembly"]
