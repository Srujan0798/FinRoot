"""Unit tests for the LLM provider layer (wave-1/01)."""

from __future__ import annotations

import pytest

from finroot.llm import LLMResult, get_provider, parse_reasoning_confidence
from finroot.llm.base import LLMProvider
from finroot.llm.mock import MockProvider
from finroot.schemas.enums import Provider

# ---------------------------------------------------------------------------
# parse_reasoning_confidence
# ---------------------------------------------------------------------------


class TestParseReasoningConfidence:
    def test_extracts_both_tags(self) -> None:
        text = "<reasoning>because X</reasoning> answer <confidence>high</confidence>"
        clean, reasoning, confidence = parse_reasoning_confidence(text)
        assert reasoning == "because X"
        assert confidence == "high"
        assert "answer" in clean
        assert "<reasoning>" not in clean

    def test_no_tags(self) -> None:
        clean, reasoning, confidence = parse_reasoning_confidence("plain text")
        assert clean == "plain text"
        assert reasoning is None
        assert confidence is None

    def test_multiline_reasoning(self) -> None:
        text = "<reasoning>\nline1\nline2\n</reasoning>\nresult\n<confidence>low</confidence>"
        clean, reasoning, confidence = parse_reasoning_confidence(text)
        assert "line1" in reasoning
        assert "line2" in reasoning
        assert confidence == "low"

    def test_case_insensitive(self) -> None:
        text = "<REASONING>r</REASONING> ok <CONFIDENCE>m</CONFIDENCE>"
        clean, reasoning, confidence = parse_reasoning_confidence(text)
        assert reasoning == "r"
        assert confidence == "m"


# ---------------------------------------------------------------------------
# MockProvider
# ---------------------------------------------------------------------------


class TestMockProvider:
    def test_deterministic(self) -> None:
        p = MockProvider()
        r1 = p.complete("hello")
        r2 = p.complete("hello")
        assert r1.text == r2.text
        assert r1.reasoning == r2.reasoning

    def test_always_has_tags(self) -> None:
        p = MockProvider()
        for prompt in ["hi", "portfolio", "risk", "tax", "market"]:
            r = p.complete(prompt)
            assert r.reasoning is not None, f"Missing reasoning for prompt={prompt!r}"
            assert r.confidence is not None, f"Missing confidence for prompt={prompt!r}"

    def test_provider_and_model(self) -> None:
        r = MockProvider().complete("test")
        assert r.provider == "mock"
        assert r.model == "mock"

    def test_result_is_llm_result(self) -> None:
        r = MockProvider().complete("test")
        assert isinstance(r, LLMResult)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class TestFactory:
    def test_default_is_mock(self) -> None:
        p = get_provider()
        assert p.name == "mock"

    def test_resolve_mock_by_string(self) -> None:
        p = get_provider("mock")
        assert p.name == "mock"

    def test_resolve_ollama_by_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        # Ollama doesn't require a key to instantiate
        p = get_provider("ollama")
        assert p.name == "ollama"

    def test_resolve_groq_by_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        p = get_provider("groq")
        assert p.name == "groq"

    def test_resolve_openai_by_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        p = get_provider("openai")
        assert p.name == "openai"

    def test_resolve_enum(self) -> None:
        p = get_provider(Provider.MOCK)
        assert p.name == "mock"

    def test_unknown_provider_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_provider("nonexistent")

    def test_env_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FINROOT_LLM_PROVIDER", "mock")
        p = get_provider()
        assert p.name == "mock"


# ---------------------------------------------------------------------------
# Real providers raise when SDK/key missing
# ---------------------------------------------------------------------------


class TestRealProvidersRequireCredentials:
    def test_groq_raises_without_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        from finroot.llm.groq import GroqProvider

        with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
            GroqProvider()

    def test_openai_raises_without_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from finroot.llm.openai import OpenAIProvider

        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            OpenAIProvider()


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    def test_mock_satisfies_protocol(self) -> None:
        p = MockProvider()
        assert isinstance(p, LLMProvider)

    def test_llm_result_forbids_extra(self) -> None:
        with pytest.raises(ValueError):
            LLMResult(
                text="x",
                provider="mock",
                model="mock",
                bogus_field="nope",
            )
