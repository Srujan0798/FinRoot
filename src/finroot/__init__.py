"""FinRoot — Sovereign Reasoning-First AI Financial Agent."""

from __future__ import annotations

from finroot.agents.base import BaseAgent
from finroot.audit.trail import AuditTrail
from finroot.llm import get_provider
from finroot.schemas import AgentState
from finroot.tools.base import BaseTool

__version__ = "0.1.0"

# config/ lives at the project root (not inside src/finroot/).
# Import conditionally so `import finroot` works even without PYTHONPATH=.
try:
    from config.settings import get_settings  # noqa: F401
except ImportError:
    get_settings = None  # type: ignore[assignment]

__all__ = [
    "get_provider",
    "AgentState",
    "AuditTrail",
    "BaseTool",
    "BaseAgent",
    "get_settings",
    "__version__",
]
