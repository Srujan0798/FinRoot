"""Tests for ResultSynthesizer (wave-4, task 06).

Covers:
* Confidence logic (HIGH / MEDIUM / LOW)
* Citation extraction from tool_outputs
* Risk flag extraction
* Reasoning step population
* No-output and all-error edge cases
* Recommendation JSON round-trip
"""

from __future__ import annotations

from datetime import UTC, datetime

from finroot.schemas.enums import ConfidenceLevel
from finroot.schemas.recommendation import Citation, Recommendation
from finroot.schemas.state import AgentState
from finroot.workflows.synthesize import ResultSynthesizer

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)
SYNTH = ResultSynthesizer()


def _citation(source: str = "market_data", value: str | None = "150.25") -> Citation:
    return Citation(
        source=source,
        detail="Latest price for AAPL",
        value=value,
        retrieved_at=UTC_NOW,
    )


def _tool_output(
    *,
    tool: str = "market_analyst",
    citations: list[Citation] | None = None,
    risk_flags: list[str] | None = None,
    type_: str = "analysis",
    output: str | None = "AAPL: $150.25, up 2.1%",
    error: str | None = None,
) -> dict:
    d: dict = {"tool": tool, "type": type_}
    if citations is not None:
        d["citations"] = citations
    if risk_flags is not None:
        d["risk_flags"] = risk_flags
    if output is not None:
        d["output"] = output
    if error is not None:
        d["type"] = "error"
        d["error"] = error
    return d


# ---------------------------------------------------------------------------
# Confidence: HIGH
# ---------------------------------------------------------------------------


class TestConfidenceHigh:
    def test_three_outputs_with_citations(self) -> None:
        state = AgentState(
            query="how is my portfolio?",
            tool_outputs=[
                _tool_output(tool="market_analyst", citations=[_citation("market_data", "150.25")]),
                _tool_output(tool="risk_assessor", citations=[_citation("risk_calc", "0.35")]),
                _tool_output(tool="tax_planner", citations=[_citation("tax_table", "15%")]),
            ],
        )
        rec = SYNTH.synthesize(state)
        assert rec.confidence is ConfidenceLevel.HIGH
        assert len(rec.citations) >= 3

    def test_four_outputs_all_cited(self) -> None:
        state = AgentState(
            query="evaluate risk",
            tool_outputs=[
                _tool_output(tool="a", citations=[_citation()]),
                _tool_output(tool="b", citations=[_citation()]),
                _tool_output(tool="c", citations=[_citation()]),
                _tool_output(tool="d", citations=[_citation()]),
            ],
        )
        rec = SYNTH.synthesize(state)
        assert rec.confidence is ConfidenceLevel.HIGH


# ---------------------------------------------------------------------------
# Confidence: MEDIUM
# ---------------------------------------------------------------------------


class TestConfidenceMedium:
    def test_one_output_with_citations(self) -> None:
        state = AgentState(
            query="check allocation",
            tool_outputs=[
                _tool_output(tool="analyst", citations=[_citation()]),
                _tool_output(tool="other", type_="info", output="no citations here"),
            ],
        )
        rec = SYNTH.synthesize(state)
        assert rec.confidence is ConfidenceLevel.MEDIUM

    def test_two_outputs_with_citations(self) -> None:
        state = AgentState(
            query="check allocation",
            tool_outputs=[
                _tool_output(tool="a", citations=[_citation("src1", "100")]),
                _tool_output(tool="b", citations=[_citation("src2", "200")]),
            ],
        )
        rec = SYNTH.synthesize(state)
        assert rec.confidence is ConfidenceLevel.MEDIUM

    def test_some_errors_some_data(self) -> None:
        state = AgentState(
            query="complex query",
            tool_outputs=[
                _tool_output(tool="ok_agent", citations=[_citation()]),
                _tool_output(tool="bad_agent", type_="error", error="timed out"),
            ],
        )
        rec = SYNTH.synthesize(state)
        assert rec.confidence is ConfidenceLevel.MEDIUM


# ---------------------------------------------------------------------------
# Confidence: LOW
# ---------------------------------------------------------------------------


class TestConfidenceLow:
    def test_no_tool_outputs(self) -> None:
        state = AgentState(query="anything")
        rec = SYNTH.synthesize(state)
        assert rec.confidence is ConfidenceLevel.LOW
        assert "don't have enough data" in rec.summary.lower()

    def test_all_errors(self) -> None:
        state = AgentState(
            query="run analysis",
            tool_outputs=[
                _tool_output(tool="agent_a", type_="error", error="outage"),
                _tool_output(tool="agent_b", type_="error", error="no data"),
            ],
        )
        rec = SYNTH.synthesize(state)
        assert rec.confidence is ConfidenceLevel.LOW

    def test_no_citations_anywhere(self) -> None:
        """Wave-13: 2 non-error outputs now produce fallback citations and
        MEDIUM confidence. The previous FM-11 "no inline citations ⇒ LOW"
        rule still applies when tool outputs themselves carry no evidence
        AND the synthesizer cannot fall back (i.e. zero outputs, or
        outputs with no observable content)."""
        # Empty tool_outputs ⇒ still LOW.
        state = AgentState(query="simple")
        assert SYNTH.synthesize(state).confidence is ConfidenceLevel.LOW

        # Outputs with output=None and no usable payload ⇒ still LOW
        # because the synthesizer's fallback requires observable content.
        state = AgentState(
            query="simple",
            tool_outputs=[
                _tool_output(tool="a", output=None, type_="empty"),
                _tool_output(tool="b", output=None, type_="empty"),
            ],
        )
        assert SYNTH.synthesize(state).confidence is ConfidenceLevel.LOW


# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------


class TestFeatures:
    def test_risk_flags_extracted(self) -> None:
        state = AgentState(
            query="flag risks",
            tool_outputs=[
                _tool_output(
                    tool="risk_agent",
                    risk_flags=["high concentration in tech", "currency exposure"],
                    citations=[_citation()],
                ),
            ],
        )
        rec = SYNTH.synthesize(state)
        assert "high concentration in tech" in rec.risks
        assert "currency exposure" in rec.risks

    def test_reasoning_steps_populated(self) -> None:
        state = AgentState(
            query="steps",
            tool_outputs=[
                _tool_output(tool="first_agent", citations=[_citation()]),
                _tool_output(tool="second_agent", type_="simulation", output="result"),
            ],
        )
        rec = SYNTH.synthesize(state)
        assert "first_agent" in rec.analysis
        assert "second_agent" in rec.analysis

    def test_errors_noted_in_reasoning(self) -> None:
        state = AgentState(
            query="with errors",
            tool_outputs=[
                _tool_output(tool="good_agent", citations=[_citation()]),
                _tool_output(tool="bad_agent", type_="error", error="API failure"),
            ],
        )
        rec = SYNTH.synthesize(state)
        assert "API failure" in rec.analysis or "bad_agent" in rec.analysis

    def test_recommendation_round_trips_through_json(self) -> None:
        state = AgentState(
            query="round trip",
            tool_outputs=[
                _tool_output(tool="agent", citations=[_citation()]),
            ],
        )
        rec = SYNTH.synthesize(state)
        json_str = rec.model_dump_json()
        rec2 = Recommendation.model_validate_json(json_str)
        assert rec2 == rec
        assert rec2.confidence is ConfidenceLevel.MEDIUM

    def test_summary_contains_confidence_and_errors(self) -> None:
        state = AgentState(
            query="summary test",
            tool_outputs=[
                _tool_output(tool="ok", citations=[_citation()]),
                _tool_output(tool="fail", type_="error", error="timeout"),
            ],
        )
        rec = SYNTH.synthesize(state)
        # Summary should contain substantive financial advice
        assert len(rec.summary) > 50, f"Summary too short: {rec.summary}"
        # Should mention errors if there were any
        assert "error" in rec.summary.lower() or "errors" in rec.summary.lower() or "failed" in rec.summary.lower()
