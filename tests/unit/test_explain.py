"""Tests for ExplainabilityAssembly (wave-5, task 05).

Minimum 10 tests covering reasoning chain, citations, confidence labels,
risk summary, principles check, and edge cases.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from finroot.reasoning.explain import ExplainabilityAssembly
from finroot.schemas.audit import AuditEvent
from finroot.schemas.state import AgentState

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)

_ZERO_HASH = "0" * 64


def _audit_event(
    seq: int,
    type_: str,
    payload: dict | None = None,
) -> AuditEvent:
    return AuditEvent(
        ts=UTC_NOW,
        seq=seq,
        type=type_,
        payload=payload or {},
        prev_hash=_ZERO_HASH,
        hash=_ZERO_HASH,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExplainabilityAssembly:
    """Tests for ExplainabilityAssembly.assemble()."""

    def setup_method(self) -> None:
        self.assembly = ExplainabilityAssembly()

    # -- 1. Reasoning chain from audit events ----------------------------

    def test_reasoning_chain_populated(self) -> None:
        """Audit events produce a reasoning chain with correct steps."""
        state = AgentState(
            query="test",
            audit_events=[
                _audit_event(0, "router.plan", {"intent": "portfolio"}),
                _audit_event(1, "tool.called", {"tool": "yfinance"}),
                _audit_event(2, "step.done", {"result": "ok"}),
            ],
        )
        result = self.assembly.assemble(state)
        chain = result["reasoning_chain"]
        assert len(chain) == 3
        assert chain[0] == {
            "step": 0,
            "action": "router.plan",
            "result": "{'intent': 'portfolio'}",
            "source": "router.plan",
        }
        assert chain[1]["step"] == 1
        assert chain[1]["action"] == "tool.called"
        assert chain[2]["step"] == 2

    def test_reasoning_chain_empty_audit(self) -> None:
        """Empty audit events produce an empty reasoning chain (not error)."""
        state = AgentState(query="test", audit_events=[])
        result = self.assembly.assemble(state)
        assert result["reasoning_chain"] == []

    # -- 2. Citations from tool outputs ----------------------------------

    def test_citations_extracted(self) -> None:
        """Tool outputs produce correct citation entries."""
        state = AgentState(
            query="test",
            tool_outputs=[
                {"tool": "yfinance", "detail": "AAPL price", "value": "150"},
                {"tool": "tax_tables", "detail": "LTCG rate", "value": "15%"},
            ],
        )
        result = self.assembly.assemble(state)
        citations = result["citations"]
        assert len(citations) == 2
        assert citations[0]["source"] == "yfinance"
        assert citations[0]["claim"] == "AAPL price"
        assert citations[0]["data"]["value"] == "150"
        assert citations[1]["source"] == "tax_tables"
        assert citations[1]["claim"] == "LTCG rate"

    def test_citations_empty_tool_outputs(self) -> None:
        """Empty tool outputs produce an empty citations list."""
        state = AgentState(query="test", tool_outputs=[])
        result = self.assembly.assemble(state)
        assert result["citations"] == []

    # -- 3. Confidence label mapping -------------------------------------

    def test_confidence_high(self) -> None:
        """Overall >= 0.7 maps to HIGH."""
        state = AgentState(
            query="test",
            critique={
                "overall": 0.85,
                "scores": [
                    {"axis": "correctness", "score": 0.9},
                    {"axis": "risk_awareness", "score": 0.8},
                ],
            },
        )
        result = self.assembly.assemble(state)
        assert result["confidence_breakdown"]["label"] == "HIGH"

    def test_confidence_medium(self) -> None:
        """0.4 <= overall < 0.7 maps to MEDIUM."""
        state = AgentState(
            query="test",
            critique={
                "overall": 0.55,
                "scores": [{"axis": "correctness", "score": 0.55}],
            },
        )
        result = self.assembly.assemble(state)
        assert result["confidence_breakdown"]["label"] == "MEDIUM"

    def test_confidence_low(self) -> None:
        """Overall < 0.4 maps to LOW."""
        state = AgentState(
            query="test",
            critique={
                "overall": 0.2,
                "scores": [{"axis": "correctness", "score": 0.2}],
            },
        )
        result = self.assembly.assemble(state)
        assert result["confidence_breakdown"]["label"] == "LOW"

    def test_confidence_boundary_high(self) -> None:
        """Overall exactly 0.7 maps to HIGH (boundary)."""
        state = AgentState(
            query="test",
            critique={
                "overall": 0.7,
                "scores": [{"axis": "correctness", "score": 0.7}],
            },
        )
        result = self.assembly.assemble(state)
        assert result["confidence_breakdown"]["label"] == "HIGH"

    def test_confidence_boundary_medium(self) -> None:
        """Overall exactly 0.4 maps to MEDIUM (boundary)."""
        state = AgentState(
            query="test",
            critique={
                "overall": 0.4,
                "scores": [{"axis": "correctness", "score": 0.4}],
            },
        )
        result = self.assembly.assemble(state)
        assert result["confidence_breakdown"]["label"] == "MEDIUM"

    def test_confidence_no_critique(self) -> None:
        """Missing critique defaults to 'not evaluated'."""
        state = AgentState(query="test")
        result = self.assembly.assemble(state)
        assert result["confidence_breakdown"]["label"] == "not evaluated"
        assert result["confidence_breakdown"]["axes"] == {}

    def test_confidence_axes_included(self) -> None:
        """Individual axis scores are present in axes dict."""
        state = AgentState(
            query="test",
            critique={
                "overall": 0.8,
                "scores": [
                    {"axis": "correctness", "score": 0.9},
                    {"axis": "risk_awareness", "score": 0.7},
                ],
            },
        )
        result = self.assembly.assemble(state)
        axes = result["confidence_breakdown"]["axes"]
        assert axes["correctness"] == 0.9
        assert axes["risk_awareness"] == 0.7

    # -- 4. Risk summary -------------------------------------------------

    def test_risk_summary_from_tool_outputs(self) -> None:
        """Risk-related tool outputs produce a non-empty risk summary."""
        state = AgentState(
            query="test",
            tool_outputs=[
                {"tool": "risk_analyzer", "detail": "Portfolio VaR is 12%"},
                {"tool": "market_data", "detail": "Market is stable"},
            ],
        )
        result = self.assembly.assemble(state)
        assert "risk" in result["risk_summary"].lower()
        assert "risk_analyzer" in result["risk_summary"]

    def test_risk_summary_no_risk_outputs(self) -> None:
        """Tool outputs without risk content produce default message."""
        state = AgentState(
            query="test",
            tool_outputs=[
                {"tool": "market_data", "detail": "Market is stable"},
            ],
        )
        result = self.assembly.assemble(state)
        assert result["risk_summary"] == "No risk-related data in tool outputs."

    def test_risk_summary_empty_tool_outputs(self) -> None:
        """Empty tool outputs produce default risk summary."""
        state = AgentState(query="test", tool_outputs=[])
        result = self.assembly.assemble(state)
        assert result["risk_summary"] == "No risk-related data in tool outputs."

    # -- 5. Principles check ---------------------------------------------

    def test_principles_check_default_when_missing(self) -> None:
        """Missing verifier_verdict defaults to compliant=True and 'not checked'."""
        state = AgentState(query="test")
        result = self.assembly.assemble(state)
        pc = result["principles_check"]
        assert pc["compliant"] is True
        assert "not checked" in pc["warnings"]

    def test_principles_check_non_compliant(self) -> None:
        """Non-compliant verifier verdict propagates warning."""
        state = AgentState(
            query="test",
            verifier_verdict={
                "compliant": False,
                "warning": "This advice may not be suitable for your profile",
            },
        )
        result = self.assembly.assemble(state)
        pc = result["principles_check"]
        assert pc["compliant"] is False
        assert "This advice may not be suitable for your profile" in pc["warnings"]

    def test_principles_check_compliant(self) -> None:
        """Compliant verdict produces no warnings list with default message."""
        state = AgentState(
            query="test",
            verifier_verdict={
                "compliant": True,
                "warning": None,
            },
        )
        result = self.assembly.assemble(state)
        pc = result["principles_check"]
        assert pc["compliant"] is True
        assert "No prudence warnings." in pc["warnings"]

    # -- 6. Full structure ------------------------------------------------

    def test_output_has_all_contract_keys(self) -> None:
        """Assemble result must contain all 5 contract fields."""
        state = AgentState(query="test")
        result = self.assembly.assemble(state)
        expected_keys = {
            "reasoning_chain",
            "risk_summary",
            "confidence_breakdown",
            "citations",
            "principles_check",
        }
        assert set(result.keys()) == expected_keys

    def test_full_state_all_fields(self) -> None:
        """End-to-end: all fields populated produces a complete trace."""
        state = AgentState(
            query="test",
            audit_events=[
                _audit_event(0, "router.plan"),
                _audit_event(1, "tool.called"),
            ],
            tool_outputs=[
                {"tool": "yfinance", "detail": "price 150", "value": "150"},
                {"tool": "risk_analyzer", "detail": "VaR 5%"},
            ],
            critique={
                "overall": 0.75,
                "scores": [
                    {"axis": "correctness", "score": 0.8},
                    {"axis": "risk_awareness", "score": 0.7},
                    {"axis": "actionability", "score": 0.6},
                    {"axis": "explainability", "score": 0.8},
                    {"axis": "evidence", "score": 0.7},
                ],
            },
            verifier_verdict={
                "compliant": True,
                "warning": None,
            },
        )
        result = self.assembly.assemble(state)
        assert len(result["reasoning_chain"]) == 2
        assert len(result["citations"]) == 2
        assert result["confidence_breakdown"]["label"] == "HIGH"
        assert result["principles_check"]["compliant"] is True
        assert "risk" in result["risk_summary"].lower()


@pytest.mark.parametrize(
    "overall, expected_label",
    [
        (1.0, "HIGH"),
        (0.7, "HIGH"),
        (0.69, "MEDIUM"),
        (0.5, "MEDIUM"),
        (0.4, "MEDIUM"),
        (0.39, "LOW"),
        (0.0, "LOW"),
    ],
)
def test_confidence_label_thresholds(overall: float, expected_label: str) -> None:
    """Parametrized boundary tests for confidence label mapping."""
    assembly = ExplainabilityAssembly()
    result = assembly._build_confidence_breakdown({
        "overall": overall,
        "scores": [{"axis": "correctness", "score": overall}],
    })
    assert result["label"] == expected_label
