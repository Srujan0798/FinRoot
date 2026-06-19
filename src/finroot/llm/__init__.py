"""FinRoot LLM provider layer.

Public API:
- :class:`LLMProvider` — protocol all adapters implement.
- :class:`LLMResult` — structured completion result.
- :func:`get_provider` — factory to resolve a provider by name.
- :func:`parse_reasoning_confidence` — extract ``<reasoning>``/``<confidence>`` tags.
"""

from __future__ import annotations

from finroot.llm.base import LLMProvider, LLMResult, parse_reasoning_confidence
from finroot.llm.factory import get_provider

__all__ = [
    "LLMProvider",
    "LLMResult",
    "get_provider",
    "parse_reasoning_confidence",
]
