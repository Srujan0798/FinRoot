"""Counterfactual explanations — "what would change this recommendation".

Analyzes a completed recommendation and generates counterfactual scenarios:
conditions under which the recommendation would be different. This helps users
understand the sensitivity and robustness of the advice.

Examples:
- "If your risk tolerance were higher, equity allocation could increase to 70%."
- "If the stock's P/E drops below 15, the recommendation would shift to BUY."
- "If you had no existing debt, the advice would change to recommend a home loan."
"""

from __future__ import annotations

import logging

from finroot.schemas.enums import ConfidenceLevel
from finroot.schemas.recommendation import Recommendation
from finroot.schemas.state import AgentState

logger = logging.getLogger(__name__)


class CounterfactualGenerator:
    """Generate counterfactual explanations for a recommendation.

    Examines the recommendation's assumptions, risks, and analysis to produce
    "what-if" scenarios that would change the advice.
    """

    def generate(self, state: AgentState) -> list[str]:
        """Generate counterfactual explanations for the current recommendation.

        Parameters
        ----------
        state:
            The fully-populated AgentState with candidate/final recommendation.

        Returns
        -------
        list[str]
            Counterfactual explanations, each describing a scenario that would
            change the recommendation.
        """
        rec = state.candidate or state.final
        if rec is None:
            return []

        counterfactuals: list[str] = []

        # 1. Derive from assumptions — if an assumption changes, advice changes
        counterfactuals.extend(self._from_assumptions(rec))

        # 2. Derive from risks — if a risk materializes, advice changes
        counterfactuals.extend(self._from_risks(rec))

        # 3. Derive from confidence level — what would increase/decrease confidence
        counterfactuals.extend(self._from_confidence(rec, state))

        # 4. Derive from invalidation conditions (if already set)
        counterfactuals.extend(rec.invalidation_conditions)

        # Deduplicate
        seen: set[str] = set()
        unique: list[str] = []
        for cf in counterfactuals:
            normalized = cf.strip().lower()
            if normalized not in seen:
                seen.add(normalized)
                unique.append(cf)

        return unique

    def _from_assumptions(self, rec: Recommendation) -> list[str]:
        """Generate counterfactuals from the recommendation's assumptions."""
        cfs: list[str] = []
        for assumption in rec.assumptions:
            lower = assumption.lower()
            # Convert assumptions into "if this weren't true" scenarios
            if "risk" in lower and ("tolerance" in lower or "profile" in lower):
                cfs.append(
                    "If your risk tolerance were different, the recommended asset "
                    "allocation would change accordingly."
                )
            elif "horizon" in lower or "tenure" in lower or "years" in lower:
                cfs.append(
                    "If your investment horizon were shorter, the recommendation "
                    "would shift toward more conservative options."
                )
            elif "income" in lower or "salary" in lower:
                cfs.append(
                    "If your income changed significantly, the tax planning and "
                    "investment amounts would need to be recalculated."
                )
            elif "inflation" in lower:
                cfs.append(
                    "If inflation were higher than assumed, real returns would be "
                    "lower and the corpus target would need to be revised upward."
                )
            elif "return" in lower or "growth" in lower:
                cfs.append(
                    "If actual returns differ from assumptions, the goal timeline "
                    "or SIP amount would need adjustment."
                )
        return cfs

    def _from_risks(self, rec: Recommendation) -> list[str]:
        """Generate counterfactuals from the recommendation's identified risks."""
        cfs: list[str] = []
        for risk in rec.risks:
            lower = risk.lower()
            if "concentration" in lower:
                cfs.append(
                    "If you diversify your portfolio, the concentration risk warning "
                    "would no longer apply."
                )
            elif "liquidity" in lower:
                cfs.append(
                    "If you maintain a larger emergency fund, liquidity risk would "
                    "be mitigated and the recommendation would change."
                )
            elif "interest rate" in lower or "rate" in lower:
                cfs.append(
                    "If interest rates move significantly, the debt/equity mix "
                    "recommendation would need to be revisited."
                )
            elif "market" in lower or "volatility" in lower:
                cfs.append(
                    "If market conditions stabilize, the risk-adjusted allocation "
                    "could be more aggressive."
                )
            elif "tax" in lower:
                cfs.append(
                    "If tax laws change (e.g., LTCG exemption limit), the tax "
                    "optimization strategy would need to be revised."
                )
        return cfs

    def _from_confidence(self, rec: Recommendation, state: AgentState) -> list[str]:
        """Generate counterfactuals based on confidence level."""
        cfs: list[str] = []

        if rec.confidence == ConfidenceLevel.LOW:
            cfs.append(
                "If more information were available about your complete financial "
                "picture, confidence in this recommendation could increase."
            )
            cfs.append(
                "If the analysis had access to real-time market data instead of "
                "estimates, the recommendation would be more precise."
            )
        elif rec.confidence == ConfidenceLevel.MEDIUM:
            cfs.append(
                "If your goals and constraints were more clearly defined, the "
                "recommendation could be more specific and actionable."
            )

        # Check if there's a twin with specific data
        twin = state.twin_snapshot
        if twin:
            if not twin.get("holdings"):
                cfs.append(
                    "If your current holdings were known, the recommendation could "
                    "include specific rebalancing actions."
                )
            if not twin.get("goals"):
                cfs.append(
                    "If your financial goals were specified, the advice could be "
                    "tailored to each goal's timeline and amount."
                )

        return cfs


__all__ = ["CounterfactualGenerator"]
