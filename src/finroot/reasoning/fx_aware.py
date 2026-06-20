"""FX-aware reasoning for multi-currency portfolios.

Analyzes portfolios with holdings in multiple currencies and provides:
- Currency risk assessment
- FX-adjusted return calculations
- Hedging recommendations
- NRI-specific tax implications

Handles common NRI scenarios:
- USD/INR exposure for US-based NRIs
- AED/INR exposure for Gulf-based NRIs
- GBP/INR exposure for UK-based NRIs
- Multi-currency portfolio diversification benefits
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class CurrencyExposure(BaseModel):
    """Represents exposure to a single currency."""

    currency: str
    amount: float
    percentage: float
    inr_equivalent: float
    risk_level: str  # low, moderate, high

    model_config = {"extra": "forbid"}


class FXAnalysis(BaseModel):
    """Complete FX analysis of a multi-currency portfolio."""

    total_inr_value: float
    currency_exposures: list[CurrencyExposure]
    fx_risk_score: float  # 0-1, higher = more FX risk
    hedging_recommended: bool
    hedging_cost_estimate: float
    currency_diversification_score: float  # 0-1, higher = more diversified
    recommendations: list[str]
    assumptions: list[str]
    citation: str

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# Mock FX rates (INR-anchored, as of 2026-06)
# ---------------------------------------------------------------------------

_MOCK_FX_RATES: dict[str, float] = {
    "USD": 83.5,
    "EUR": 90.2,
    "GBP": 106.0,
    "JPY": 0.56,
    "AED": 22.7,
    "SGD": 62.3,
    "CAD": 61.8,
    "AUD": 54.2,
    "CHF": 94.5,
    "INR": 1.0,
}


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------


class FxAwareAnalyzer:
    """Analyze multi-currency portfolios for FX risk and opportunities.

    Works with mock rates in offline mode. Can be extended to use live rates.
    """

    def analyze(self, holdings: list[dict[str, Any]], base_currency: str = "INR") -> FXAnalysis:
        """Analyze FX exposure of a portfolio.

        Parameters
        ----------
        holdings:
            List of holdings with at least 'currency', 'amount', and optionally
            'symbol', 'asset_class', 'weight'.
        base_currency:
            The base currency for reporting (default INR).

        Returns
        -------
        FXAnalysis
            Complete FX analysis with exposures, risks, and recommendations.
        """
        if not holdings:
            return self._empty_analysis()

        # Calculate INR equivalents
        exposures: list[CurrencyExposure] = []
        total_inr = 0.0

        for h in holdings:
            ccy = h.get("currency", "INR").upper()
            amount = float(h.get("amount", h.get("market_value", 0)))
            rate = _MOCK_FX_RATES.get(ccy, 1.0)
            inr_eq = amount * rate if ccy != "INR" else amount
            total_inr += inr_eq

            exposures.append(CurrencyExposure(
                currency=ccy,
                amount=amount,
                percentage=0.0,  # Calculated below
                inr_equivalent=inr_eq,
                risk_level=self._currency_risk(ccy),
            ))

        # Calculate percentages
        for exp in exposures:
            exp.percentage = round(exp.inr_equivalent / total_inr * 100, 2) if total_inr > 0 else 0.0

        # Aggregate by currency
        aggregated = self._aggregate_exposures(exposures)

        # Calculate risk scores
        fx_risk = self._calculate_fx_risk(aggregated, total_inr)
        div_score = self._calculate_diversification_score(aggregated)
        hedge_recommended = fx_risk > 0.3  # Recommend hedging if >30% non-INR

        # Generate recommendations
        recommendations = self._generate_recommendations(
            aggregated, total_inr, fx_risk, hedge_recommended
        )

        # Build assumptions
        assumptions = [
            f"Base currency: {base_currency}",
            "FX rates: mock fixed table (2026-06)",
            "Currency risk is measured by non-base currency exposure",
            "Hedging cost estimated at 2-4% p.a. for major currencies",
            "No consideration of currency correlation with asset returns",
        ]

        # Build citation
        foreign_pct = sum(e.percentage for e in aggregated if e.currency != base_currency)
        citation = (
            f"FX analysis: {len(holdings)} holdings across {len(aggregated)} currencies. "
            f"Non-{base_currency} exposure: {foreign_pct:.1f}% of portfolio. "
            f"FX risk score: {fx_risk:.2f}. "
            f"Diversification score: {div_score:.2f}."
        )

        return FXAnalysis(
            total_inr_value=round(total_inr, 2),
            currency_exposures=aggregated,
            fx_risk_score=round(fx_risk, 2),
            hedging_recommended=hedge_recommended,
            hedging_cost_estimate=round(total_inr * 0.03 * (foreign_pct / 100), 2),  # ~3% of foreign exposure
            currency_diversification_score=round(div_score, 2),
            recommendations=recommendations,
            assumptions=assumptions,
            citation=citation,
        )

    def _empty_analysis(self) -> FXAnalysis:
        """Return an empty analysis for portfolios with no holdings."""
        return FXAnalysis(
            total_inr_value=0.0,
            currency_exposures=[],
            fx_risk_score=0.0,
            hedging_recommended=False,
            hedging_cost_estimate=0.0,
            currency_diversification_score=0.0,
            recommendations=["No holdings to analyze for FX exposure."],
            assumptions=["Empty portfolio - no FX analysis performed."],
            citation="No holdings provided for FX analysis.",
        )

    def _aggregate_exposures(self, exposures: list[CurrencyExposure]) -> list[CurrencyExposure]:
        """Aggregate multiple exposures in the same currency."""
        agg: dict[str, CurrencyExposure] = {}
        for exp in exposures:
            if exp.currency in agg:
                existing = agg[exp.currency]
                existing.amount += exp.amount
                existing.inr_equivalent += exp.inr_equivalent
            else:
                agg[exp.currency] = CurrencyExposure(
                    currency=exp.currency,
                    amount=exp.amount,
                    percentage=exp.percentage,
                    inr_equivalent=exp.inr_equivalent,
                    risk_level=exp.risk_level,
                )

        # Recalculate percentages
        total = sum(e.inr_equivalent for e in agg.values())
        for e in agg.values():
            e.percentage = round(e.inr_equivalent / total * 100, 2) if total > 0 else 0.0

        return sorted(agg.values(), key=lambda e: e.percentage, reverse=True)

    def _currency_risk(self, currency: str) -> str:
        """Assess risk level for a currency."""
        # Major currencies: lower risk
        major = {"USD", "EUR", "GBP", "JPY", "CHF"}
        # Emerging market / volatile: higher risk
        emerging = {"INR", "BRL", "ZAR", "TRY", "RUB"}

        if currency in major:
            return "low"
        elif currency in emerging:
            return "moderate"
        else:
            return "high"

    def _calculate_fx_risk(self, exposures: list[CurrencyExposure], total: float) -> float:
        """Calculate overall FX risk score (0-1)."""
        if total <= 0:
            return 0.0

        # Sum of non-INR exposures weighted by risk level
        risk_weights = {"low": 0.3, "moderate": 0.6, "high": 1.0}
        weighted_risk = 0.0

        for exp in exposures:
            if exp.currency != "INR":
                weight = risk_weights.get(exp.risk_level, 0.5)
                weighted_risk += (exp.inr_equivalent / total) * weight

        return min(weighted_risk, 1.0)

    def _calculate_diversification_score(self, exposures: list[CurrencyExposure]) -> float:
        """Calculate currency diversification score (0-1).

        Higher score = more diversified across currencies.
        Uses inverse Herfindahl-Hirschman Index (HHI).
        """
        if len(exposures) <= 1:
            return 0.0

        # Calculate HHI (sum of squared percentages)
        hhi = sum((e.percentage / 100) ** 2 for e in exposures)

        # Normalize: 1 currency = HHI=1, N equal currencies = HHI=1/N
        # Inverse and normalize to 0-1
        n = len(exposures)
        min_hhi = 1.0 / n
        max_hhi = 1.0

        if max_hhi == min_hhi:
            return 0.0

        # Score: 1 = perfectly diversified, 0 = single currency
        score = (max_hhi - hhi) / (max_hhi - min_hhi)
        return max(0.0, min(1.0, score))

    def _generate_recommendations(
        self,
        exposures: list[CurrencyExposure],
        total: float,
        fx_risk: float,
        hedge_recommended: bool,
    ) -> list[str]:
        """Generate FX-related recommendations."""
        recs: list[str] = []

        # Check for concentration in single foreign currency
        for exp in exposures:
            if exp.currency != "INR" and exp.percentage > 50:
                recs.append(
                    f"High concentration in {exp.currency} ({exp.percentage:.1f}%). "
                    f"Consider diversifying across other currencies to reduce FX risk."
                )

        # Hedging recommendation
        if hedge_recommended:
            foreign_pct = sum(e.percentage for e in exposures if e.currency != "INR")
            recs.append(
                f"Non-INR exposure is {foreign_pct:.1f}%. Consider partial FX hedging "
                f"to reduce currency volatility. Estimated hedging cost: 2-4% p.a."
            )

        # NRI-specific advice
        for exp in exposures:
            if exp.currency == "USD" and exp.percentage > 30:
                recs.append(
                    "For USD-heavy portfolios, consider maintaining some INR exposure "
                    "for Indian expenses and goals. INR typically depreciates 3-5% p.a. "
                    "against USD, which can work in your favor for India-bound remittances."
                )
            elif exp.currency == "AED" and exp.percentage > 30:
                recs.append(
                    "AED is pegged to USD, so USD/AED risk is minimal. However, "
                    "INR/AED fluctuations can impact India-bound remittances. "
                    "Consider timing large transfers for favorable rates."
                )

        # Diversification benefit
        if len(exposures) >= 3:
            div_currencies = [e.currency for e in exposures if e.currency != "INR"]
            recs.append(
                f"Currency diversification across {', '.join(div_currencies)} provides "
                f"natural hedging. Correlations between these currencies are typically low."
            )

        if not recs:
            recs.append(
                "FX exposure is well-managed. No immediate currency-related actions needed."
            )

        return recs


__all__ = ["FxAwareAnalyzer", "FXAnalysis", "CurrencyExposure"]
