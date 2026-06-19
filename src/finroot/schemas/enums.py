"""Core enums for FinRoot.

Frozen by `.specify/specs/wave-1/contracts/schemas.contract.md`. Names and values
are part of the contract; changes require an orchestrator ADR.
"""

from __future__ import annotations

from enum import Enum


class Intent(str, Enum):  # noqa: UP042  (contract: str, Enum)
    """User's intent behind a query, classified by the router."""

    PORTFOLIO = "portfolio"
    RISK = "risk"
    TAX = "tax"
    NEWS_IMPACT = "news_impact"
    CASHFLOW = "cashflow"
    CREDIT = "credit"
    GENERAL = "general"


class Domain(str, Enum):  # noqa: UP042  (contract: str, Enum)
    """Financial domain a piece of evidence or analysis belongs to."""

    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    DERIVATIVE = "derivative"
    COMMODITY = "commodity"
    FX = "fx"
    CRYPTO = "crypto"
    REAL_ESTATE = "real_estate"
    CASH = "cash"
    MACRO = "macro"
    TAX = "tax"
    OTHER = "other"


class ConfidenceLevel(str, Enum):  # noqa: UP042  (contract: str, Enum)
    """How confident the agent is in its recommendation.

    `INSUFFICIENT` means the agent should recommend "do not act yet" rather than
    guessing — structural enforcement of FM-11.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


class RiskBand(str, Enum):  # noqa: UP042  (contract: str, Enum)
    """Risk classification of a position, portfolio, or scenario."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"


class Provider(str, Enum):  # noqa: UP042  (contract: str, Enum)
    """LLM provider identifier. MOCK is the offline / judging default."""

    MOCK = "mock"
    OLLAMA = "ollama"
    GROQ = "groq"
    OPENAI = "openai"


__all__ = [
    "ConfidenceLevel",
    "Domain",
    "Intent",
    "Provider",
    "RiskBand",
]
