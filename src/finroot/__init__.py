"""FinRoot — Sovereign Reasoning-First AI Financial Agent."""

from __future__ import annotations

from config.settings import get_settings

from finroot.agents.base import BaseAgent
from finroot.audit.trail import AuditTrail
from finroot.llm import get_provider
from finroot.schemas import AgentState
from finroot.schemas.enums import (
    Provider,  # noqa: F401 — load schemas first so config can import them
)
from finroot.tools.base import BaseTool

__version__ = "0.1.0"

__all__ = [
    "get_provider",
    "AgentState",
    "AuditTrail",
    "BaseTool",
    "BaseAgent",
    "get_settings",
    "__version__",
]
