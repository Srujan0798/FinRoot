"""Ollama LLM provider — local sovereign default.

Requires the ``ollama`` Python package and a running Ollama server.
The SDK is **lazy-imported** so the Mock provider never needs it.
"""

from __future__ import annotations

import os

from finroot.llm.base import LLMResult, parse_reasoning_confidence

_DEFAULT_MODEL = os.environ.get("FINROOT_OLLAMA_MODEL", "llama3")


class OllamaProvider:
    """Thin adapter around the ``ollama`` Python SDK."""

    name: str = "ollama"

    def __init__(self, model: str | None = None, host: str | None = None) -> None:
        self.model = model or _DEFAULT_MODEL
        self.host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResult:
        try:
            import ollama as ollama_sdk  # noqa: F811
        except ImportError as exc:
            raise RuntimeError(
                "The 'ollama' package is required for OllamaProvider. "
                "Install it with: pip install ollama"
            ) from exc

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        client = ollama_sdk.Client(host=self.host)
        response = client.chat(
            model=self.model,
            messages=messages,
            options={"temperature": temperature, "num_predict": max_tokens},
        )
        raw: str = response["message"]["content"]
        clean, reasoning, confidence = parse_reasoning_confidence(raw)
        return LLMResult(
            text=clean,
            reasoning=reasoning,
            confidence=confidence,
            provider="ollama",
            model=self.model,
            tokens=None,
        )


__all__ = ["OllamaProvider"]
