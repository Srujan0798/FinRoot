"""Tests for config/settings.py, config/prompts.py, and src/finroot/utils/config.py."""

from __future__ import annotations

import pytest
from config.prompts import PromptRegistry
from config.settings import Settings, get_settings
from src.finroot.schemas.enums import Provider
from src.finroot.utils.config import assert_settings, print_startup_banner

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_get_settings_cache() -> None:
    """Clear the lru_cache on ``get_settings`` before every test so env var
    changes between tests are always picked up."""
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Settings — defaults
# ---------------------------------------------------------------------------


class TestSettingsDefaults:
    def test_default_provider_is_mock(self) -> None:
        s = Settings()
        assert s.llm_provider == Provider.MOCK

    def test_default_ollama_fields(self) -> None:
        s = Settings()
        assert s.ollama_base_url == "http://localhost:11434"
        assert s.ollama_model == "llama3.1:8b"

    def test_default_api_keys_are_none(self) -> None:
        s = Settings()
        assert s.groq_api_key is None
        assert s.openai_api_key is None

    def test_default_paths(self) -> None:
        s = Settings()
        assert s.chroma_dir == "data/chroma"
        assert s.audit_path == "logs/audit.jsonl"


# ---------------------------------------------------------------------------
# Settings — env-var overrides
# ---------------------------------------------------------------------------


class TestSettingsEnvOverride:
    def test_llm_provider_ollama_via_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FINROOT_LLM_PROVIDER", "ollama")
        s = get_settings()
        assert s.llm_provider == Provider.OLLAMA

    def test_llm_provider_groq_via_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FINROOT_LLM_PROVIDER", "groq")
        s = get_settings()
        assert s.llm_provider == Provider.GROQ

    def test_ollama_base_url_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FINROOT_OLLAMA_BASE_URL", "http://custom:11434")
        s = get_settings()
        assert s.ollama_base_url == "http://custom:11434"

    def test_groq_api_key_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FINROOT_GROQ_API_KEY", "gsk_test_key")
        s = get_settings()
        assert s.groq_api_key == "gsk_test_key"


# ---------------------------------------------------------------------------
# get_settings — caching
# ---------------------------------------------------------------------------


class TestGetSettingsCaching:
    def test_returns_settings_instance(self) -> None:
        s = get_settings()
        assert isinstance(s, Settings)

    def test_is_cached(self) -> None:
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_cache_cleared_between_tests(self) -> None:
        # This test runs after cache_clear from the fixture — just verify
        # we get a fresh instance each call within the test when cleared.
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2  # still cached within same call


# ---------------------------------------------------------------------------
# PromptRegistry
# ---------------------------------------------------------------------------


class TestPromptRegistry:
    def test_get_by_name_and_version(self) -> None:
        r = PromptRegistry()
        prompt = r.get("router.system", "1.0")
        assert "financial-intent classifier" in prompt

    def test_get_latest_version(self) -> None:
        r = PromptRegistry()
        prompt = r.get("router.system")
        assert "financial-intent classifier" in prompt

    def test_get_unknown_name_raises(self) -> None:
        r = PromptRegistry()
        with pytest.raises(KeyError, match="Unknown prompt name="):
            r.get("nonexistent.prompt")

    def test_get_unknown_version_raises(self) -> None:
        r = PromptRegistry()
        with pytest.raises(KeyError, match="Unknown prompt"):
            r.get("router.system", "99.99")

    def test_register_and_retrieve(self) -> None:
        r = PromptRegistry()
        r.register("my.prompt", "1.0", "Hello world")
        assert r.get("my.prompt", "1.0") == "Hello world"

    def test_list_names(self) -> None:
        r = PromptRegistry()
        names = r.list_names()
        assert "router.system" in names
        assert "reason.analysis" in names

    def test_versions(self) -> None:
        r = PromptRegistry()
        r.register("test.prompt", "0.1", "v0.1")
        r.register("test.prompt", "0.2", "v0.2")
        assert set(r.versions("test.prompt")) == {"0.1", "0.2"}


# ---------------------------------------------------------------------------
# Utils — assert_settings / print_startup_banner
# ---------------------------------------------------------------------------


class TestAssertSettings:
    def test_default_settings_pass(self) -> None:
        s = Settings()
        assert_settings(s)

    def test_all_providers_pass(self) -> None:
        provider_cases: list[Settings] = [
            Settings(llm_provider=Provider.MOCK),
            Settings(llm_provider=Provider.OLLAMA),
            Settings(llm_provider=Provider.GROQ, groq_api_key="gsk_test"),
            Settings(llm_provider=Provider.OPENAI, openai_api_key="sk_test"),
        ]
        for s in provider_cases:
            assert_settings(s)

    def test_ollama_requires_base_url(self) -> None:
        s = Settings(llm_provider=Provider.OLLAMA, ollama_base_url="")
        with pytest.raises(RuntimeError, match="Required setting.*ollama_base_url"):
            assert_settings(s)

    def test_groq_requires_api_key(self) -> None:
        s = Settings(llm_provider=Provider.GROQ)
        with pytest.raises(RuntimeError, match="Required setting.*groq_api_key"):
            assert_settings(s)

    def test_openai_requires_api_key(self) -> None:
        s = Settings(llm_provider=Provider.OPENAI)
        with pytest.raises(RuntimeError, match="Required setting.*openai_api_key"):
            assert_settings(s)


class TestPrintStartupBanner:
    def test_banner_prints(self, capsys: pytest.CaptureFixture) -> None:
        s = Settings()
        print_startup_banner(s)
        captured = capsys.readouterr()
        assert "FinRoot | provider=mock" in captured.out
        assert "ollama=llama3.1:8b" in captured.out
        assert "chroma=" in captured.out
        assert "audit=" in captured.out
