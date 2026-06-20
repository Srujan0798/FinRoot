"""Goal-based financial planning tool.

Calculates the required monthly SIP, target corpus, and timeline for specific
financial goals like retirement, child's education, home purchase, etc.

Uses standard financial planning formulas:
- Future Value of SIP: FV = P * [(1 + r)^n - 1] / r * (1 + r)
- Present Value of corpus: PV = FV / (1 + inflation)^n
- Required SIP: P = FV * r / [(1 + r)^n - 1] / (1 + r)

All calculations assume monthly compounding and inflation adjustment.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from finroot.tools.base import BaseTool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# I/O types
# ---------------------------------------------------------------------------


class GoalInput(BaseModel):
    """Input for goal-based planning calculation."""

    goal_name: str = Field(
        min_length=1,
        description="Name of the financial goal (e.g., 'Retirement', 'Child Education')",
    )
    target_amount: float = Field(
        gt=0,
        description="Target amount needed for the goal in today's rupees",
    )
    years_to_goal: int = Field(
        ge=1,
        le=50,
        description="Number of years until the goal is needed",
    )
    inflation_rate: float = Field(
        default=0.06,
        ge=0.0,
        le=0.15,
        description="Expected inflation rate (default 6% for India)",
    )
    expected_return: float = Field(
        default=0.12,
        ge=0.01,
        le=0.30,
        description="Expected annual return on investments (default 12% for equity-heavy)",
    )
    existing_corpus: float = Field(
        default=0.0,
        ge=0.0,
        description="Amount already saved towards this goal",
    )
    existing_sip: float = Field(
        default=0.0,
        ge=0.0,
        description="Monthly SIP already running for this goal",
    )
    risk_profile: str = Field(
        default="moderate",
        description="Risk profile: conservative, moderate, aggressive",
    )

    model_config = {"extra": "forbid"}


class GoalOutput(BaseModel):
    """Output of goal-based planning calculation."""

    goal_name: str
    target_amount_today: float
    target_amount_future: float
    inflation_adjusted: bool
    years_to_goal: int
    required_monthly_sip: float
    existing_corpus_future_value: float
    existing_sip_future_value: float
    gap_amount: float
    recommended_allocation: dict[str, float]
    assumptions: list[str]
    citation: str

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class GoalPlannerTool(BaseTool[GoalInput, GoalOutput]):
    """Goal-based financial planning calculator.

    Calculates:
    - Inflation-adjusted target corpus
    - Required monthly SIP to reach the goal
    - Future value of existing investments
    - Gap between current trajectory and goal
    - Recommended asset allocation based on risk profile and time horizon
    """

    name = "goal_planner"

    def __init__(self, audit: Any = None, mock: bool = False) -> None:
        super().__init__(audit=audit)
        self.mock = mock

    def _run(self, inp: GoalInput) -> GoalOutput:
        # Calculate inflation-adjusted target
        inflation_factor = (1 + inp.inflation_rate) ** inp.years_to_goal
        target_future = inp.target_amount * inflation_factor

        # Future value of existing corpus
        return_factor = (1 + inp.expected_return) ** inp.years_to_goal
        existing_corpus_fv = inp.existing_corpus * return_factor

        # Future value of existing SIP (FV of annuity)
        monthly_return = inp.expected_return / 12
        n_months = inp.years_to_goal * 12
        existing_sip_fv = self._fv_of_sip(inp.existing_sip, monthly_return, n_months)

        # Gap to fill
        gap = target_future - existing_corpus_fv - existing_sip_fv
        if gap < 0:
            gap = 0.0  # Already on track or over-funded

        # Required SIP to fill the gap
        required_sip = self._required_sip(gap, monthly_return, n_months)

        # Recommended allocation based on risk profile and time horizon
        allocation = self._recommended_allocation(inp.risk_profile, inp.years_to_goal)

        # Build assumptions
        assumptions = [
            f"Inflation rate: {inp.inflation_rate:.1%} p.a.",
            f"Expected return: {inp.expected_return:.1%} p.a.",
            f"Time horizon: {inp.years_to_goal} years",
            f"Risk profile: {inp.risk_profile}",
            "Returns are compounded monthly",
            "SIP is invested at the start of each month",
            "No withdrawal during the accumulation phase",
        ]

        if inp.existing_corpus > 0:
            assumptions.append(f"Existing corpus: ₹{inp.existing_corpus:,.0f}")
        if inp.existing_sip > 0:
            assumptions.append(f"Existing SIP: ₹{inp.existing_sip:,.0f}/month")

        citation = (
            f"Goal planning for '{inp.goal_name}': target ₹{inp.target_amount:,.0f} "
            f"in {inp.years_to_goal} years. Inflation-adjusted target: ₹{target_future:,.0f}. "
            f"Required SIP: ₹{required_sip:,.0f}/month at {inp.expected_return:.1%} expected return. "
            "Past performance does not guarantee future returns."
        )

        return GoalOutput(
            goal_name=inp.goal_name,
            target_amount_today=inp.target_amount,
            target_amount_future=round(target_future, 2),
            inflation_adjusted=True,
            years_to_goal=inp.years_to_goal,
            required_monthly_sip=round(required_sip, 2),
            existing_corpus_future_value=round(existing_corpus_fv, 2),
            existing_sip_future_value=round(existing_sip_fv, 2),
            gap_amount=round(gap, 2),
            recommended_allocation=allocation,
            assumptions=assumptions,
            citation=citation,
        )

    @staticmethod
    def _fv_of_sip(monthly_amount: float, monthly_rate: float, n_months: int) -> float:
        """Calculate future value of a series of monthly SIPs."""
        if monthly_amount <= 0:
            return 0.0
        if monthly_rate <= 0:
            return monthly_amount * n_months
        # FV = P * [(1 + r)^n - 1] / r * (1 + r)
        return monthly_amount * ((1 + monthly_rate) ** n_months - 1) / monthly_rate * (1 + monthly_rate)

    @staticmethod
    def _required_sip(target_fv: float, monthly_rate: float, n_months: int) -> float:
        """Calculate required monthly SIP to reach a target future value."""
        if target_fv <= 0:
            return 0.0
        if monthly_rate <= 0:
            return target_fv / n_months if n_months > 0 else 0.0
        # P = FV * r / [(1 + r)^n - 1] / (1 + r)
        return target_fv * monthly_rate / ((1 + monthly_rate) ** n_months - 1) / (1 + monthly_rate)

    @staticmethod
    def _recommended_allocation(risk_profile: str, years: int) -> dict[str, float]:
        """Recommend asset allocation based on risk profile and time horizon.

        Conservative: 30% equity, 60% debt, 10% gold
        Moderate: 50% equity, 40% debt, 10% gold
        Aggressive: 70% equity, 20% debt, 10% gold

        Adjust based on time horizon:
        - Short (<5 years): More conservative
        - Medium (5-15 years): As per risk profile
        - Long (>15 years): Can be more aggressive
        """
        base = {
            "conservative": {"equity": 0.30, "debt": 0.60, "gold": 0.10},
            "moderate": {"equity": 0.50, "debt": 0.40, "gold": 0.10},
            "aggressive": {"equity": 0.70, "debt": 0.20, "gold": 0.10},
        }

        alloc = base.get(risk_profile.lower(), base["moderate"])

        # Adjust for time horizon
        if years < 5:
            # Short term: more conservative
            alloc["equity"] = max(alloc["equity"] - 0.20, 0.10)
            alloc["debt"] = min(alloc["debt"] + 0.20, 0.80)
        elif years > 15:
            # Long term: can be more aggressive
            alloc["equity"] = min(alloc["equity"] + 0.10, 0.80)
            alloc["debt"] = max(alloc["debt"] - 0.10, 0.10)

        # Normalize to sum to 1.0
        total = sum(alloc.values())
        return {k: round(v / total, 2) for k, v in alloc.items()}


__all__ = ["GoalPlannerTool", "GoalInput", "GoalOutput"]
