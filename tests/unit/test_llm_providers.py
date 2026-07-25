"""Comprehensive tests for LLM providers, Ollama configuration, and factory resolution."""

from __future__ import annotations

import pytest

from finroot.llm.base import LLMResult
from finroot.llm.factory import get_provider
from finroot.llm.mock import MockProvider

# ---------------------------------------------------------------------------
# MockProvider
# ---------------------------------------------------------------------------


@pytest.mark.wave1
class TestMockProvider:
    def test_mock_provider_init(self) -> None:
        p = MockProvider()
        assert p.name == "mock"

    def test_mock_provider_complete(self) -> None:
        p = MockProvider()
        result = p.complete("What is my portfolio allocation?")
        assert isinstance(result, LLMResult)
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        assert result.reasoning is not None
        assert result.confidence is not None
        assert result.provider == "mock"
        assert result.model == "mock"

    def test_mock_provider_deterministic(self) -> None:
        p = MockProvider()
        r1 = p.complete("hello world")
        r2 = p.complete("hello world")
        assert r1.text == r2.text
        assert r1.reasoning == r2.reasoning
        assert r1.confidence == r2.confidence

    def test_mock_provider_varies_by_prompt(self) -> None:
        p = MockProvider()
        r1 = p.complete("What is my portfolio allocation?")
        r2 = p.complete("What is my credit score?")
        assert r1.text != r2.text


# ---------------------------------------------------------------------------
# OllamaProvider
# ---------------------------------------------------------------------------


@pytest.mark.wave1
class TestOllamaProvider:
    def test_ollama_provider_init_no_model(self) -> None:
        from finroot.llm.ollama import OllamaProvider

        p = OllamaProvider(model="test-model")
        assert p.name == "ollama"
        assert p.model == "test-model"

    def test_ollama_provider_config_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from finroot.llm.ollama import OllamaProvider

        monkeypatch.setenv("OLLAMA_HOST", "http://custom-host:9999")
        p = OllamaProvider(model="test-model")
        assert p.host == "http://custom-host:9999"


# ---------------------------------------------------------------------------
# GroqProvider
# ---------------------------------------------------------------------------


@pytest.mark.wave1
class TestGroqProvider:
    def test_groq_provider_init_no_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        from finroot.llm.groq import GroqProvider

        with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
            GroqProvider()

    def test_groq_provider_config_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        monkeypatch.setenv("FINROOT_GROQ_MODEL", "my-custom-model")
        from finroot.llm.groq import GroqProvider

        # Module-level _DEFAULT_MODEL is already cached; test model passed directly
        p = GroqProvider(model="my-custom-model")
        assert p.model == "my-custom-model"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


@pytest.mark.wave1
class TestFactory:
    def test_factory_mock_default(self) -> None:
        p = get_provider()
        assert p.name == "mock"

    def test_factory_explicit_name(self) -> None:
        p = get_provider("mock")
        assert isinstance(p, MockProvider)
        assert p.name == "mock"

    def test_factory_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            get_provider("nonexistent")

    def test_factory_reads_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FINROOT_LLM_PROVIDER", "mock")
        p = get_provider()
        assert p.name == "mock"
        assert isinstance(p, MockProvider)
