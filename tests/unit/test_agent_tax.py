"""Tests for TaxPlannerAgent (wave-4, task 04).

Minimum 10 tests covering:
- TaxPlanner with LTCG gain → correct tax in tool_outputs
- TaxPlanner with STCG gain → correct tax
- TaxPlanner with missing gain info → diagnostic output
- Audit trail entries
- Agent name correct
"""

from __future__ import annotations

from pathlib import Path
from tempfile import mkdtemp

import pytest

from finroot.agents.tax_agent import TaxPlannerAgent
from finroot.audit.trail import AuditTrail
from finroot.llm.mock import MockProvider
from finroot.schemas.state import AgentState
from finroot.tools.profile import UserProfileTool
from finroot.tools.tax import TaxRuleTool

# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def audit() -> AuditTrail:
    tmpdir = Path(mkdtemp())
    return AuditTrail(tmpdir / "audit.jsonl")


@pytest.fixture
def agent_with_audit(audit: AuditTrail) -> TaxPlannerAgent:
    return TaxPlannerAgent(
        llm=MockProvider(),
        tools=[
            TaxRuleTool(audit=audit),
            UserProfileTool(audit=audit),
        ],
        audit=audit,
    )


@pytest.fixture
def agent_no_profile() -> TaxPlannerAgent:
    return TaxPlannerAgent(
        llm=MockProvider(),
        tools=[
            TaxRuleTool(),
            UserProfileTool(),
        ],
    )


# ======================================================================
# Tax computation tests
# ======================================================================


class TestTaxComputation:
    """Correct tax amounts and breakdowns."""

    def test_ltcg_correct_tax(self, agent_with_audit, audit):
        """LTCG gain produces correct tax breakdown in tool_outputs."""
        state = AgentState(
            query="tax on LTCG",
            twin_snapshot={
                "gain": 200000.0,
                "gain_type": "LTCG",
                "annual_income": 1_800_000.0,
            },
        )
        result = agent_with_audit.act(state)

        tax_outs = [o for o in result.tool_outputs if o.get("type") == "tax_computation"]
        assert len(tax_outs) == 1
        t = tax_outs[0]
        assert t["agent"] == "tax_planner"
        assert t["gain"] == 200000.0
        assert t["gain_type"] == "LTCG"
        assert t["tax_amount"] == pytest.approx(10400.0, rel=1e-6)
        assert t["effective_rate_pct"] == pytest.approx(5.2, rel=1e-6)
        assert t["breakdown"]["base_tax"] == pytest.approx(10000.0, rel=1e-6)
        assert t["breakdown"]["cess"] == pytest.approx(400.0, rel=1e-6)
        assert t["breakdown"]["surcharge"] == pytest.approx(0.0, rel=1e-6)
        assert "LTCG_EQUITY" in t["rule_applied"]

    def test_stcg_equity_correct_tax(self, agent_with_audit, audit):
        """STCG_EQUITY gain produces correct tax breakdown."""
        state = AgentState(
            query="tax on STCG equity",
            twin_snapshot={
                "gain": 50000.0,
                "gain_type": "STCG_EQUITY",
                "annual_income": 1_800_000.0,
            },
        )
        result = agent_with_audit.act(state)

        tax_outs = [o for o in result.tool_outputs if o.get("type") == "tax_computation"]
        assert len(tax_outs) == 1
        t = tax_outs[0]
        assert t["gain"] == 50000.0
        assert t["gain_type"] == "STCG_EQUITY"
        assert t["tax_amount"] == pytest.approx(7800.0, rel=1e-6)
        assert t["effective_rate_pct"] == pytest.approx(15.6, rel=1e-6)
        assert t["breakdown"]["base_tax"] == pytest.approx(7500.0, rel=1e-6)
        assert t["breakdown"]["cess"] == pytest.approx(300.0, rel=1e-6)

    def test_stcg_non_equity_slab_rate(self, agent_with_audit, audit):
        """STCG (debt/gold) uses income slab rate."""
        state = AgentState(
            query="tax on STCG debt",
            twin_snapshot={
                "gain": 100000.0,
                "gain_type": "STCG",
                "annual_income": 1_800_000.0,
            },
        )
        result = agent_with_audit.act(state)

        tax_outs = [o for o in result.tool_outputs if o.get("type") == "tax_computation"]
        assert len(tax_outs) == 1
        t = tax_outs[0]
        assert t["tax_amount"] == pytest.approx(31200.0, rel=1e-6)
        assert t["effective_rate_pct"] == pytest.approx(31.2, rel=1e-6)
        assert t["breakdown"]["base_tax"] == pytest.approx(30000.0, rel=1e-6)

    def test_ltcg_below_exemption(self, agent_with_audit, audit):
        """LTCG gain below exemption limit results in zero tax."""
        state = AgentState(
            query="small LTCG gain",
            twin_snapshot={
                "gain": 50000.0,
                "gain_type": "LTCG",
                "annual_income": 1_000_000.0,
            },
        )
        result = agent_with_audit.act(state)

        tax_outs = [o for o in result.tool_outputs if o.get("type") == "tax_computation"]
        assert len(tax_outs) == 1
        t = tax_outs[0]
        assert t["tax_amount"] == pytest.approx(0.0, rel=1e-6)
        assert t["breakdown"]["taxable_gain"] == 0.0


# ======================================================================
# Missing / invalid input tests
# ======================================================================


class TestMissingInput:
    """Diagnostic outputs when input is incomplete."""

    def test_missing_gain_produces_diagnostic(self, agent_no_profile):
        """No gain amount → diagnostic in tool_outputs."""
        state = AgentState(
            query="what is my tax?",
            twin_snapshot={"gain_type": "LTCG"},
        )
        result = agent_no_profile.act(state)

        diags = [o for o in result.tool_outputs if o.get("type") == "diagnostic"]
        assert len(diags) == 1
        assert "gain amount" in diags[0]["message"]

    def test_missing_gain_type_produces_diagnostic(self, agent_no_profile):
        """No gain type → diagnostic in tool_outputs."""
        state = AgentState(
            query="tax on 100000",
            twin_snapshot={"gain": 100000.0},
        )
        result = agent_no_profile.act(state)

        diags = [o for o in result.tool_outputs if o.get("type") == "diagnostic"]
        assert len(diags) == 1
        assert "gain type" in diags[0]["message"]

    def test_invalid_gain_type_produces_diagnostic(self, agent_no_profile):
        """Unrecognized gain type → diagnostic."""
        state = AgentState(
            query="weird gain",
            twin_snapshot={
                "gain": 100000.0,
                "gain_type": "ULTRA_LTCG",
            },
        )
        result = agent_no_profile.act(state)

        diags = [o for o in result.tool_outputs if o.get("type") == "diagnostic"]
        assert len(diags) == 1
        assert "unrecognized" in diags[0]["message"].lower()

    def test_missing_income_produces_diagnostic(self, agent_no_profile):
        """No income data → diagnostic."""
        state = AgentState(
            query="tax on LTCG",
            twin_snapshot={
                "gain": 100000.0,
                "gain_type": "LTCG",
            },
        )
        result = agent_no_profile.act(state)

        diags = [o for o in result.tool_outputs if o.get("type") == "diagnostic"]
        assert len(diags) == 1
        assert "income" in diags[0]["message"].lower()


# ======================================================================
# Query parsing tests
# ======================================================================


class TestQueryParsing:
    """Gain info extracted from query text."""

    def test_query_parsing_ltcg(self, agent_no_profile):
        """LTCG gain info parsed from query."""
        state = AgentState(
            query="What is the tax on \u20b95,00,000 LTCG from equity?",
        )
        result = agent_no_profile.act(state)

        diags = [o for o in result.tool_outputs if o.get("type") == "diagnostic"]
        # Should complain about missing income, not missing gain
        diag_messages = [d["message"] for d in diags]
        income_diags = [m for m in diag_messages if "income" in m.lower()]
        assert len(income_diags) >= 1


# ======================================================================
# Profile tool integration tests
# ======================================================================


class TestProfileIntegration:
    """UserProfileTool calls when snapshot lacks income."""

    def test_annual_income_from_profile_tool(self, audit):
        """TaxPlanner loads annual_income via UserProfileTool from JSON."""
        agent = TaxPlannerAgent(
            llm=MockProvider(),
            tools=[
                TaxRuleTool(audit=audit),
                UserProfileTool(audit=audit),
            ],
            audit=audit,
        )
        state = AgentState(
            query="tax on LTCG for Priya",
            twin_snapshot={
                "gain": 200000.0,
                "gain_type": "LTCG",
                "user_id": "twin_priya_sharma_001",
            },
        )
        result = agent.act(state)

        tax_outs = [o for o in result.tool_outputs if o.get("type") == "tax_computation"]
        assert len(tax_outs) == 1
        t = tax_outs[0]
        assert t["tax_amount"] == pytest.approx(10400.0, rel=1e-6)


# ======================================================================
# Audit trail tests
# ======================================================================


class TestAuditTrail:
    """Audit trail entries generated by tool calls."""

    def test_audit_trail_entries(self, agent_with_audit, audit):
        """Tool calls produce audit trail entries."""
        state = AgentState(
            query="tax on LTCG",
            twin_snapshot={
                "gain": 200000.0,
                "gain_type": "LTCG",
                "annual_income": 1_800_000.0,
            },
        )
        agent_with_audit.act(state)

        events = audit.replay()
        tool_called = [e for e in events if e.type == "tool.called"]
        assert len(tool_called) >= 1
        assert tool_called[0].payload["tool"] == "tax_rule"


# ======================================================================
# Agent metadata tests
# ======================================================================


class TestAgentMetadata:
    """Agent identity and construction."""

    def test_agent_name_correct(self):
        """Agent name is 'tax_planner'."""
        agent = TaxPlannerAgent(llm=MockProvider())
        assert agent.name == "tax_planner"

    def test_default_tools(self):
        """Agent creates default tools when none provided."""
        agent = TaxPlannerAgent(llm=MockProvider())
        assert len(agent.tools) == 2
        tool_names = {t.name for t in agent.tools}
        assert tool_names == {"tax_rule", "user_profile"}

    def test_custom_tools(self):
        """Agent accepts custom tool list."""
        tr = TaxRuleTool()
        agent = TaxPlannerAgent(llm=MockProvider(), tools=[tr])
        assert len(agent.tools) == 1
        assert agent.tools[0].name == "tax_rule"
