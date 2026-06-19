"""Mock LLM provider — deterministic, offline, no network.

Responses are keyed by prompt hash so the same prompt always produces the same
output. Always embeds ``<reasoning>`` and ``<confidence>`` tags so downstream
parsing is exercised in every test.
"""

from __future__ import annotations

import hashlib

from finroot.llm.base import LLMResult, parse_reasoning_confidence

# Five canned responses rotated by prompt hash modulo 5.
_CANNED: list[str] = [
    (
        "<reasoning>The user sent a short greeting. No financial analysis "
        "is needed.</reasoning>\nHello! How can I help with your finances today?"
        "\n<confidence>high</confidence>"
    ),
    (
        "<reasoning>The query touches portfolio allocation. Without specific "
        "holdings I can only give general guidance.</reasoning>\nDiversification "
        "across asset classes reduces idiosyncratic risk."
        "\n<confidence>medium</confidence>"
    ),
    (
        "<reasoning>Risk assessment requires concrete position data. This is a "
        "placeholder response for offline testing.</reasoning>\nRisk cannot be "
        "quantified without portfolio details."
        "\n<confidence>low</confidence>"
    ),
    (
        "<reasoning>Tax optimisation depends on jurisdiction and holding period. "
        "Generic advice: harvest losses to offset gains.</reasoning>\nConsider "
        "tax-loss harvesting before year-end."
        "\n<confidence>medium</confidence>"
    ),
    (
        "<reasoning>General financial query. Providing a safe, cited response."
        "</reasoning>\nMarkets are influenced by macro factors including interest "
        "rates, inflation, and geopolitical events."
        "\n<confidence>medium</confidence>"
    ),
]


class MockProvider:
    """Deterministic offline provider for tests and judging."""

    name: str = "mock"

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResult:
        idx = int(hashlib.sha256(prompt.encode()).hexdigest(), 16) % len(_CANNED)
        raw = _CANNED[idx]
        clean, reasoning, confidence = parse_reasoning_confidence(raw)
        return LLMResult(
            text=clean,
            reasoning=reasoning,
            confidence=confidence,
            provider="mock",
            model="mock",
            tokens=None,
        )


__all__ = ["MockProvider"]
