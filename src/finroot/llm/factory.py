"""Provider factory — resolves a provider name to an :class:`LLMProvider` instance.

Resolution order:
1. Explicit *name* argument (string or :class:`Provider` enum).
2. ``FINROOT_LLM_PROVIDER`` environment variable.
3. ``"mock"`` (offline default for tests).
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from finroot.schemas.enums import Provider

if TYPE_CHECKING:
    from finroot.llm.base import LLMProvider

_PROVIDER_MAP: dict[str, type] = {}


def _lazy_map() -> dict[str, type]:
    """Build the name → class mapping on first use (avoids circular imports)."""
    if not _PROVIDER_MAP:
        from finroot.llm.groq import GroqProvider
        from finroot.llm.mock import MockProvider
        from finroot.llm.ollama import OllamaProvider
        from finroot.llm.openai import OpenAIProvider

        _PROVIDER_MAP.update(
            {
                Provider.MOCK: MockProvider,
                Provider.OLLAMA: OllamaProvider,
                Provider.GROQ: GroqProvider,
                Provider.OPENAI: OpenAIProvider,
            }
        )
    return _PROVIDER_MAP


def get_provider(name: str | Provider | None = None) -> LLMProvider:
    """Return an instantiated provider.

    Raises :class:`ValueError` if *name* is unknown, or :class:`RuntimeError`
    if the provider's SDK is missing or required credentials are not set.
    """
    if name is None:
        name = os.environ.get("FINROOT_LLM_PROVIDER", Provider.MOCK)

    key = name.value if isinstance(name, Provider) else str(name).strip().lower()

    mapping = _lazy_map()
    cls = mapping.get(key)
    if cls is None:
        valid = ", ".join(sorted(mapping))
        raise ValueError(f"Unknown LLM provider {name!r}. Valid providers: {valid}")

    return cls()


__all__ = ["get_provider"]
