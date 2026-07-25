"""IntentClassifier — priority-scored keyword/pattern intent classification.

Classifies user queries into the :class:`~finroot.schemas.enums.Intent` enum
and extracts financial entities (tickers, timeframes).

Contract: `.specify/specs/wave-4/contracts/graph.contract.md` § 1.

Wave-ultra: multi-keyword scoring + tie-break priority so RISK/TAX beat
generic stock/market/news first-match footguns (GP-4, GP-5).
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from finroot.schemas.enums import Intent

_SYMBOL_RE: re.Pattern[str] = re.compile(
    r"\b([A-Z]{2,12}(?:\.NS|\.BO)?)\b"
)
_TIMEFRAME_RE: re.Pattern[str] = re.compile(
    r"\b(\d+)\s*(day|days|week|weeks|month|months|year|years)\b",
    re.IGNORECASE,
)

# Finance jargon / tax codes that look like tickers but are not.
_SYMBOL_DENYLIST: frozenset[str] = frozenset({
    "LTCG", "STCG", "ETF", "SIP", "STP", "SWP", "NAV", "VAR", "HHI",
    "ROI", "EMI", "GDP", "RBI", "SEBI", "NPS", "PPF", "EPF", "ELSS",
    "HRA", "TDS", "GST", "INR", "USD", "API", "LLM", "FY", "ITR",
    "VDA", "ULIP", "REIT", "LRS", "DTAA", "CII", "FNO", "NFO",
    "THE", "AND", "FOR", "MY", "OR", "TO", "OF", "IN", "ON", "IS",
    "WHAT", "HOW", "SHOULD", "CAN", "WILL", "FROM", "WITH", "THIS",
    "THAT", "HAVE", "HAS", "ARE", "WAS", "BE", "ALL", "NOT", "DO",
})

# Higher = wins ties. RISK_PRUDENCE > TAX > PORTFOLIO > RISK_METRICS >
# CREDIT > NEWS > CASHFLOW > GENERAL
_TIE_PRIORITY: dict[Intent, int] = {
    Intent.RISK: 100,
    Intent.TAX: 90,
    Intent.PORTFOLIO: 80,
    Intent.CREDIT: 70,
    Intent.NEWS_IMPACT: 60,
    Intent.CASHFLOW: 50,
    Intent.GENERAL: 10,
}

# (keywords, intent, weight for exact word-boundary match)
# Partial (substring) match scores weight * 0.7
_KEYWORD_RULES: list[tuple[list[str], Intent, float]] = [
    # --- RISK prudence / leverage (highest semantic weight) ---
    (
        [
            "emergency fund", "small-cap", "small cap", "penny stock", "all in",
            "entire savings", "life savings", "all my savings", "borrow to invest",
            "loan to invest", "loan to buy", "leverage", "margin trade", "f&o",
            "futures and options", "10x", "all-in", "yolo",
        ],
        Intent.RISK,
        12.0,
    ),
    # Compound: debt used to buy risk assets
    (
        [
            "loan to buy stock", "loan to buy stocks", "personal loan to buy",
            "borrow money to invest", "borrow to buy", "margin to buy",
        ],
        Intent.RISK,
        15.0,
    ),
    # --- RISK metrics ---
    (
        ["var", "value-at-risk", "value at risk", "drawdown", "max drawdown",
         "volatility", "sharpe", "beta", "hhi", "stress test", "stress-test"],
        Intent.RISK,
        11.0,
    ),
    (["risk", "risky", "downside"], Intent.RISK, 6.0),
    # --- TAX ---
    (
        ["tax", "capital gains", "ltcg", "stcg", "tax-loss", "tax loss",
         "harvest", "80c", "80ccd", "80d", "indexation", "cess"],
        Intent.TAX,
        10.0,
    ),
    # --- PORTFOLIO ---
    (
        ["portfolio", "allocation", "rebalance", "rebalancing", "diversif",
         "asset allocation", "holdings"],
        Intent.PORTFOLIO,
        8.0,
    ),
    # --- NEWS / policy (specific before generic market words) ---
    (
        ["rbi policy", "policy change", "policy changes", "regulatory",
         "regulation", "announcement", "rate decision", "monetary policy",
         "fiscal policy", "repo rate", "rate cut", "rate hike"],
        Intent.NEWS_IMPACT,
        9.0,
    ),
    (
        ["news", "sentiment", "headline", "breaking", "earnings call"],
        Intent.NEWS_IMPACT,
        7.0,
    ),
    (
        ["impact", "effect", "implication", "consequence", "fallout", "reaction"],
        Intent.NEWS_IMPACT,
        4.0,
    ),
    (
        ["price", "market", "stock", "stocks", "fundamental", "pe ratio",
         "earnings", "sector"],
        Intent.NEWS_IMPACT,
        3.0,
    ),
    # --- CASHFLOW ---
    (
        ["cashflow", "cash flow", "income", "expense", "budget", "sip"],
        Intent.CASHFLOW,
        7.0,
    ),
    # --- CREDIT (plain loan without invest/stock → credit) ---
    (
        ["credit", "loan", "emi", "debt", "cibil", "credit card"],
        Intent.CREDIT,
        7.0,
    ),
    # --- GENERAL ---
    (
        ["guarantee", "guaranteed", "guarantees"],
        Intent.GENERAL,
        5.0,
    ),
    (
        ["hello", "help", "hey", "greet", "hi "],
        Intent.GENERAL,
        4.0,
    ),
]


class IntentResult(BaseModel):
    """Immutable result of intent classification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    entities: dict[str, Any]
    reasoning: str


class IntentClassifier:
    """Classify user query into Intent enum + extract entities.

    Multi-keyword score: every matching rule adds weight; highest score wins.
    Ties broken by :data:`_TIE_PRIORITY` (RISK/TAX beat NEWS/PORTFOLIO).
    Confidence: 1.0 if best exact match, 0.7 if only partial, 0.5 default.
    """

    def classify(self, query: str) -> IntentResult:
        """Classify *query* and return an :class:`IntentResult`."""
        if not isinstance(query, str):
            raise TypeError(f"query must be str, got {type(query).__name__}")

        lower = query.lower()
        entities = self._extract_entities(query)

        # Compound risk: loan/borrow + stock/invest/equity
        if self._is_leverage_invest_query(lower):
            return IntentResult(
                intent=Intent.RISK,
                confidence=1.0,
                entities=entities,
                reasoning=(
                    "Leverage/borrow-to-invest pattern matched — routed to RISK "
                    "for prudence engagement"
                ),
            )

        scores: dict[Intent, float] = {}
        best_kw: dict[Intent, str] = {}
        exact_hit: dict[Intent, bool] = {}

        for keywords, intent, weight in _KEYWORD_RULES:
            for kw in keywords:
                pattern = re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
                if pattern.search(lower):
                    add = weight
                    is_exact = True
                elif kw in lower:
                    add = weight * 0.7
                    is_exact = False
                else:
                    continue
                prev = scores.get(intent, 0.0)
                scores[intent] = prev + add
                if intent not in best_kw or add >= weight * 0.99:
                    best_kw[intent] = kw
                    exact_hit[intent] = is_exact

        if not scores:
            return IntentResult(
                intent=Intent.GENERAL,
                confidence=0.5,
                entities=entities,
                reasoning="No keyword match; defaulting to GENERAL",
            )

        # Winner: max score, then tie-break priority
        def sort_key(item: tuple[Intent, float]) -> tuple[float, int]:
            intent, score = item
            return (score, _TIE_PRIORITY.get(intent, 0))

        winner, win_score = max(scores.items(), key=sort_key)
        conf = 1.0 if exact_hit.get(winner, False) else 0.7
        # Cap partial multi-hits still as high confidence when score strong
        if win_score >= 10.0:
            conf = 1.0

        kw = best_kw.get(winner, "?")
        return IntentResult(
            intent=winner,
            confidence=conf,
            entities=entities,
            reasoning=(
                f"Scored intent {winner.value}={win_score:.1f} "
                f"(top keyword '{kw}'); scores={{{self._fmt_scores(scores)}}}"
            ),
        )

    @staticmethod
    def _fmt_scores(scores: dict[Intent, float]) -> str:
        parts = [f"{k.value}:{v:.1f}" for k, v in sorted(scores.items(), key=lambda x: -x[1])]
        return ", ".join(parts[:6])

    @staticmethod
    def _is_leverage_invest_query(lower: str) -> bool:
        debt = any(
            t in lower
            for t in (
                "loan", "borrow", "leverage", "margin", "credit card debt",
            )
        )
        invest = any(
            t in lower
            for t in (
                "stock", "stocks", "equity", "invest", "crypto", "share",
                "shares", "mutual fund", "sip",
            )
        )
        return debt and invest

    # ------------------------------------------------------------------
    # Entity extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_entities(query: str) -> dict[str, Any]:
        """Extract financial entities from *query*.

        Returns a dict with ``symbols`` (list[str]) and ``timeframe``
        (str | None). Filters denylisted finance jargon mistaken for tickers.
        """
        raw_symbols = _SYMBOL_RE.findall(query)
        symbols = [s for s in raw_symbols if s.upper() not in _SYMBOL_DENYLIST]
        tf_match = _TIMEFRAME_RE.search(query)
        timeframe: str | None = None
        if tf_match:
            num = tf_match.group(1)
            unit = tf_match.group(2).lower()
            timeframe = f"{num} {unit}"
            if num != "1" and not unit.endswith("s"):
                timeframe += "s"

        return {"symbols": symbols, "timeframe": timeframe}


__all__ = ["IntentClassifier", "IntentResult"]
