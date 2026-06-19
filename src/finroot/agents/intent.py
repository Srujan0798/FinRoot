"""IntentClassifier — deterministic keyword/pattern-based intent classification.

Classifies user queries into the :class:`~finroot.schemas.enums.Intent` enum
and extracts financial entities (tickers, timeframes).

Contract: `.specify/specs/wave-4/contracts/graph.contract.md` § 1.
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

_KEYWORD_MAP: list[tuple[list[str], Intent]] = [
    (["portfolio", "allocation", "holdings", "rebalance", "diversif"], Intent.PORTFOLIO),
    (["risk", "var", "volatility", "drawdown", "beta", "sharpe"], Intent.RISK),
    (["tax", "capital gains", "ltcg", "stcg", "tax-loss", "tax loss", "harvest"], Intent.TAX),
    (["price", "market", "stock", "fundamental", "pe ratio", "earnings", "sector"], Intent.NEWS_IMPACT),
    (["news", "sentiment", "impact", "headline"], Intent.NEWS_IMPACT),
    (["cashflow", "cash flow", "income", "expense", "budget"], Intent.CASHFLOW),
    (["credit", "loan", "emi", "debt"], Intent.CREDIT),
    (["hello", "help", "hey", "greet"], Intent.GENERAL),
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

    Uses deterministic keyword/pattern matching — no LLM needed in mock mode.
    Confidence: 1.0 for exact keyword match, 0.7 for partial, 0.5 for default.
    """

    def classify(self, query: str) -> IntentResult:
        """Classify *query* and return an :class:`IntentResult`.

        Parameters
        ----------
        query:
            The raw user query string.

        Returns
        -------
        IntentResult
            With intent, confidence, extracted entities, and reasoning.

        Raises
        ------
        TypeError
            If *query* is not a ``str``.
        """
        if not isinstance(query, str):
            raise TypeError(f"query must be str, got {type(query).__name__}")

        lower = query.lower()
        entities = self._extract_entities(query)

        for keywords, intent in _KEYWORD_MAP:
            for kw in keywords:
                pattern = re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE)
                if pattern.search(lower):
                    return IntentResult(
                        intent=intent,
                        confidence=1.0,
                        entities=entities,
                        reasoning=f"Keyword '{kw}' matched for intent {intent.value}",
                    )
                if kw in lower:
                    return IntentResult(
                        intent=intent,
                        confidence=0.7,
                        entities=entities,
                        reasoning=f"Partial keyword '{kw}' matched for intent {intent.value}",
                    )

        return IntentResult(
            intent=Intent.GENERAL,
            confidence=0.5,
            entities=entities,
            reasoning="No keyword match; defaulting to GENERAL",
        )

    # ------------------------------------------------------------------
    # Entity extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_entities(query: str) -> dict[str, Any]:
        """Extract financial entities from *query*.

        Returns a dict with ``symbols`` (list[str]) and ``timeframe``
        (str | None).
        """
        symbols = _SYMBOL_RE.findall(query)
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
