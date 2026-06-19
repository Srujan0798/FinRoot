"""OpenAI LLM provider.

Requires the ``openai`` package and the ``OPENAI_API_KEY`` environment variable.
The SDK is **lazy-imported** so the Mock provider never needs it.
"""

from __future__ import annotations

import os

from finroot.llm.base import LLMResult, parse_reasoning_confidence

_DEFAULT_MODEL = os.environ.get("FINROOT_OPENAI_MODEL", "gpt-4o-mini")


class OpenAIProvider:
    """Thin adapter around the ``openai`` Python SDK."""

    name: str = "openai"

    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model or _DEFAULT_MODEL
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is required for OpenAIProvider. "
                "Set it or pass api_key explicitly."
            )

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResult:
        try:
            from openai import OpenAI  # noqa: F811
        except ImportError as exc:
            raise RuntimeError(
                "The 'openai' package is required for OpenAIProvider. "
                "Install it with: pip install openai"
            ) from exc

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        client = OpenAI(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        raw: str = response.choices[0].message.content
        clean, reasoning, confidence = parse_reasoning_confidence(raw)
        return LLMResult(
            text=clean,
            reasoning=reasoning,
            confidence=confidence,
            provider="openai",
            model=self.model,
            tokens=response.usage.total_tokens if response.usage else None,
        )


__all__ = ["OpenAIProvider"]
