"""LLM provider abstraction — protocol, result model, and tag parser.

Every adapter implements :class:`LLMProvider`. Downstream code programs against
this protocol so providers are interchangeable at runtime.
"""

from __future__ import annotations

import re
from collections.abc import Generator
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict


class LLMResult(BaseModel):
    """Structured return from any LLM completion call."""

    model_config = ConfigDict(extra="forbid")

    text: str
    reasoning: str | None = None
    confidence: str | None = None
    provider: str
    model: str
    tokens: int | None = None


# Regex for <reasoning>…</reasoning> and <confidence>…</confidence> tags.
_RE_REASONING = re.compile(r"<reasoning>\s*(.*?)\s*</reasoning>", re.DOTALL | re.IGNORECASE)
_RE_CONFIDENCE = re.compile(r"<confidence>\s*(.*?)\s*</confidence>", re.DOTALL | re.IGNORECASE)


def parse_reasoning_confidence(text: str) -> tuple[str, str | None, str | None]:
    """Extract ``<reasoning>`` and ``<confidence>`` tags from *text*.

    Returns ``(clean_text, reasoning, confidence)`` where *clean_text* has the
    tags stripped and *reasoning*/*confidence* are the inner content or ``None``.
    """
    reasoning_match = _RE_REASONING.search(text)
    confidence_match = _RE_CONFIDENCE.search(text)

    reasoning = reasoning_match.group(1).strip() if reasoning_match else None
    confidence = confidence_match.group(1).strip() if confidence_match else None

    clean = _RE_REASONING.sub("", text)
    clean = _RE_CONFIDENCE.sub("", clean)
    clean = clean.strip()

    return clean, reasoning, confidence


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal contract every LLM adapter must satisfy."""

    name: str

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResult:
        """Send *prompt* (with optional *system* message) and return an :class:`LLMResult`."""
        ...

    def stream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> Generator[str, None, None]:
        """Yield text chunks as they arrive. Default falls back to complete()."""
        result = self.complete(
            prompt, system=system, temperature=temperature, max_tokens=max_tokens
        )
        yield result.text
