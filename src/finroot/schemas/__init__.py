"""FinRoot core schemas.

The typed spine of the system. Every wave-1+ task imports from here. Names
and field types are frozen by `.specify/specs/wave-1/contracts/schemas.contract.md`
— deviations require an ADR, not a worker choice.
"""

from __future__ import annotations

from finroot.schemas.audit import AuditEvent
from finroot.schemas.enums import (
    ConfidenceLevel,
    Domain,
    Intent,
    Provider,
    RiskBand,
)
from finroot.schemas.finance import (
    Holding,
    Horizon,
    Money,
    Portfolio,
)
from finroot.schemas.recommendation import Citation, Recommendation
from finroot.schemas.state import AgentState

__all__ = [
    "AgentState",
    "AuditEvent",
    "Citation",
    "ConfidenceLevel",
    "Domain",
    "Holding",
    "Horizon",
    "Intent",
    "Money",
    "Portfolio",
    "Provider",
    "Recommendation",
    "RiskBand",
]
