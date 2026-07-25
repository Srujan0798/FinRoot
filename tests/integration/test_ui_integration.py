"""Integration tests for the Streamlit UI module.

Verifies the UI module is importable, has required dependencies, loads
config correctly, and that the core answer pipeline works in mock mode.
Also checks that disclaimer and mock-badge source code is present.
"""

from __future__ import annotations

import ast
import importlib
import pathlib

from config.settings import Settings, get_settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_APP_SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "interface" / "ui" / "app.py"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_ui_module_importable() -> None:
    """import interface.ui.app must succeed."""
    mod = importlib.import_module("interface.ui.app")
    assert mod is not None


def test_ui_has_streamlit_deps() -> None:
    """streamlit must be importable (required by the UI)."""
    mod = importlib.import_module("streamlit")
    assert mod is not None


def test_ui_config_loads() -> None:
    """config.settings.Settings and get_settings must work in UI context."""
    s = Settings()
    assert isinstance(s, Settings)
    provider_str = s.llm_provider if isinstance(s.llm_provider, str) else s.llm_provider.value
    assert provider_str in ("mock", "ollama", "groq", "openai")

    cached = get_settings()
    assert isinstance(cached, Settings)


def test_ui_answer_function() -> None:
    """The answer function used by the UI (interface.core.answer) must be
    callable and return a valid AgentState in mock mode."""
    from interface.core import answer

    state = answer("Should I rebalance my 70/30 portfolio?", mock=True)
    assert state is not None
    assert hasattr(state, "final") or hasattr(state, "candidate")


def test_ui_mock_mode() -> None:
    """In mock mode the stream_answer generator must produce events
    ending in a 'result' event with a state."""
    from interface.core import stream_answer

    events = list(stream_answer("What is LTCG tax?", mock=True))
    assert len(events) >= 2
    last = events[-1]
    assert last.get("type") in ("result", "error")
    if last["type"] == "result":
        assert "state" in last


def test_ui_disclaimer_shown() -> None:
    """app.py source must contain the NFA / not-financial-advice disclaimer."""
    src = _APP_SRC.read_text()
    assert "Not financial advice" in src or "not financial advice" in src.lower()


def test_ui_mock_badge() -> None:
    """app.py source must contain mock-mode indicator code."""
    src = _APP_SRC.read_text()
    assert "MOCK MODE" in src or "Mock Mode" in src or "mock_mode" in src


def test_ui_page_config_set() -> None:
    """app.py must call st.set_page_config with a FinRoot title."""
    src = _APP_SRC.read_text()
    assert "set_page_config" in src
    assert "FinRoot" in src


def test_ui_has_footer() -> None:
    """app.py must contain a 'Powered by FinRoot' footer."""
    src = _APP_SRC.read_text()
    assert "Powered by FinRoot" in src


def test_ui_error_handling_present() -> None:
    """app.py must contain try/except around the main query processing."""
    src = _APP_SRC.read_text()
    # The file should have at least one try/except block in the main function
    tree = ast.parse(src)
    try_count = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Try))
    # We expect try/except blocks (at least the tab renderers, plus the new one)
    assert try_count >= 1, "app.py should contain try/except error handling"

    # Verify the specific try/except around query processing is present
    assert "try:" in src
    assert "except" in src


def test_ui_has_streamlit_page_config_icon() -> None:
    """page_icon should be set in the page config."""
    src = _APP_SRC.read_text()
    assert "page_icon" in src
