"""Groq LLM provider — fast inference via Groq cloud.

Requires the ``groq`` package and the ``GROQ_API_KEY`` environment variable.
The SDK is **lazy-imported** so the Mock provider never needs it.
"""

from __future__ import annotations

import os

from finroot.llm.base import LLMResult, parse_reasoning_confidence

_DEFAULT_MODEL = os.environ.get("FINROOT_GROQ_MODEL", "llama3-8b-8192")


class GroqProvider:
    """Thin adapter around the ``groq`` Python SDK."""

    name: str = "groq"

    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        self.model = model or _DEFAULT_MODEL
        self._api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self._api_key:
            raise RuntimeError(
                "GROQ_API_KEY environment variable is required for GroqProvider. "
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
            from groq import Groq  # noqa: F811
        except ImportError as exc:
            raise RuntimeError(
                "The 'groq' package is required for GroqProvider. "
                "Install it with: pip install groq"
            ) from exc

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        client = Groq(api_key=self._api_key)
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
            provider="groq",
            model=self.model,
            tokens=response.usage.total_tokens if response.usage else None,
        )


__all__ = ["GroqProvider"]
