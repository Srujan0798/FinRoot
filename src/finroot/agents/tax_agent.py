"""TaxPlannerAgent — ReAct sub-agent for Indian tax planning.

Computes capital gains tax using TaxRuleTool and reads user profile via
UserProfileTool. Runs on TAX intent. Max 2 ReAct iterations: profile → compute.
"""

from __future__ import annotations

import contextlib
import logging
import re
from typing import Any

from finroot.agents.base import BaseAgent
from finroot.audit.trail import AuditTrail
from finroot.llm.base import LLMProvider
from finroot.schemas.state import AgentState
from finroot.tools.base import BaseTool, ToolCallError
from finroot.tools.profile import ProfileReadInput, UserProfileTool
from finroot.tools.tax import TaxInput, TaxRuleTool

logger = logging.getLogger(__name__)

_VALID_GAIN_TYPES = frozenset({"LTCG", "STCG", "STCG_EQUITY"})

_GAIN_TYPE_KEYWORDS: dict[str, str] = {
    "long term capital gain": "LTCG",
    "ltcg": "LTCG",
    "short term capital gain": "STCG",
    "stcg equity": "STCG_EQUITY",
    "short term equity": "STCG_EQUITY",
    "stcg": "STCG",
}


def _parse_gain_from_query(query: str) -> dict[str, Any]:
    """Extract gain amount and type from query text.

    Returns partial dict (may lack ``gain`` or ``gain_type``).
    """
    result: dict[str, Any] = {}

    amount_match = re.search(
        r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)",
        query,
        re.IGNORECASE,
    )
    if amount_match:
        raw = amount_match.group(1).replace(",", "")
        with contextlib.suppress(ValueError):
            result["gain"] = float(raw)

    for keyword, gain_type in _GAIN_TYPE_KEYWORDS.items():
        if keyword in query.lower():
            result["gain_type"] = gain_type
            break

    return result


def _annual_income_from_profile(profile_data: dict[str, Any]) -> float | None:
    """Extract annual income from profile data dict.

    Checks ``annual_income`` first, then ``monthly_income * 12``, then
    ``tax_bracket_pct`` (heuristic fallback).
    """
    annual = profile_data.get("annual_income")
    if annual is not None:
        return float(annual)
    monthly = profile_data.get("monthly_income")
    if monthly is not None:
        return float(monthly) * 12.0
    return None


class TaxPlannerAgent(BaseAgent):
    """ReAct sub-agent for Indian capital-gains tax planning.

    Tools:
        - TaxRuleTool: deterministic capital gains tax calculator
        - UserProfileTool: reads DigitalTwin profile for income data
    """

    name = "tax_planner"

    def __init__(
        self,
        llm: LLMProvider,
        tools: list[BaseTool] | None = None,
        audit: AuditTrail | None = None,
    ) -> None:
        _tools = tools or [
            TaxRuleTool(audit=audit),
            UserProfileTool(audit=audit),
        ]
        super().__init__(llm=llm, tools=_tools, audit=audit)

    def act(self, state: AgentState) -> AgentState:
        """Execute the tax-planning ReAct loop.

        Iteration 1 — load user profile for annual income.
        Iteration 2 — compute capital gains tax via TaxRuleTool.
        """
        gain_info = self._extract_gain_info(state)
        gain = gain_info.get("gain")
        gain_type = gain_info.get("gain_type")
        user_id = gain_info.get("user_id", "default")

        if gain is None or gain_type is None:
            missing = []
            if gain is None:
                missing.append("gain amount")
            if gain_type is None:
                missing.append("gain type (LTCG/STCG/STCG_EQUITY)")
            state.tool_outputs.append({
                "agent": self.name,
                "type": "diagnostic",
                "message": (
                    f"TaxPlannerAgent: missing required input — {', '.join(missing)}. "
                    "Please provide the capital gain amount and type, e.g. "
                    "'\u20b91,00,000 LTCG from equity'."
                ),
            })
            return state

        if gain_type not in _VALID_GAIN_TYPES:
            state.tool_outputs.append({
                "agent": self.name,
                "type": "diagnostic",
                "message": (
                    f"TaxPlannerAgent: unrecognized gain type '{gain_type}'. "
                    f"Valid types: {', '.join(sorted(_VALID_GAIN_TYPES))}."
                ),
            })
            return state

        annual_income = self._load_annual_income(state, user_id)
        if annual_income is None:
            state.tool_outputs.append({
                "agent": self.name,
                "type": "diagnostic",
                "message": (
                    "TaxPlannerAgent: could not determine annual income "
                    f"for user_id={user_id!r}. "
                    "Please update your profile with income information."
                ),
            })
            return state

        self._compute_tax(state, gain, gain_type, annual_income)
        return state

    # ------------------------------------------------------------------
    # Data extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_gain_info(state: AgentState) -> dict[str, Any]:
        """Extract gain amount, type, and user_id from state.

        Priority: twin_snapshot → tool_outputs → query parsing.
        """
        snapshot = state.twin_snapshot
        if isinstance(snapshot, dict):
            gain = snapshot.get("gain")
            gain_type = snapshot.get("gain_type")
            if gain is not None and gain_type is not None:
                return {
                    "gain": float(gain),
                    "gain_type": str(gain_type),
                    "user_id": str(snapshot.get("user_id", "default")),
                }

        for out in state.tool_outputs:
            gain = out.get("gain")
            gain_type = out.get("gain_type")
            if gain is not None and gain_type is not None:
                return {
                    "gain": float(gain),
                    "gain_type": str(gain_type),
                    "user_id": str(out.get("user_id", "default")),
                }

        result = _parse_gain_from_query(state.query)
        result.setdefault("user_id", "default")
        if result.get("gain") is not None and result.get("gain_type") is not None:
            return result

        result.setdefault("gain", None)
        result.setdefault("gain_type", None)
        return result

    @staticmethod
    def _annual_income_from_snapshot(state: AgentState) -> float | None:
        """Check twin_snapshot for annual income data."""
        snapshot = state.twin_snapshot
        if not isinstance(snapshot, dict):
            return None
        return _annual_income_from_profile(snapshot)

    def _load_annual_income(self, state: AgentState, user_id: str) -> float | None:
        """Load annual income, preferring twin_snapshot, then UserProfileTool."""
        income = self._annual_income_from_snapshot(state)
        if income is not None:
            return income

        try:
            result = self._call_tool(
                state,
                "user_profile",
                ProfileReadInput(user_id=user_id),
            )
            return _annual_income_from_profile(result.data)
        except (ToolCallError, Exception) as exc:
            logger.warning("UserProfileTool call failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Tax computation
    # ------------------------------------------------------------------

    def _compute_tax(
        self,
        state: AgentState,
        gain: float,
        gain_type: str,
        annual_income: float,
    ) -> None:
        """Call TaxRuleTool and record structured output."""
        try:
            result = self._call_tool(
                state,
                "tax_rule",
                TaxInput(
                    gain=gain,
                    gain_type=gain_type,
                    annual_income=annual_income,
                    cess=True,
                ),
            )
            state.tool_outputs.append({
                "agent": self.name,
                "type": "tax_computation",
                "gain": gain,
                "gain_type": gain_type,
                "annual_income": annual_income,
                "tax_amount": result.tax_amount,
                "effective_rate_pct": result.effective_rate_pct,
                "breakdown": result.breakdown,
                "rule_applied": result.rule_applied,
                "citation": result.citation,
            })
        except Exception as exc:
            logger.error("TaxPlannerAgent tax computation failed: %s", exc)
            state.tool_outputs.append({
                "agent": self.name,
                "type": "error",
                "error": f"Tax computation failed: {exc}",
            })


__all__ = ["TaxPlannerAgent"]
