"""Tests for scripts/capture_screenshots.py.

Covers module imports, SCREENSHOTS list shape, output paths, and graceful
handling when Playwright is absent.
"""

from __future__ import annotations

import builtins
import sys

import pytest


class TestCaptureScreenshots:
    """Tests for the screenshot capture script."""

    def test_module_imports(self) -> None:
        """The script can be imported and exposes expected attributes."""
        import scripts.capture_screenshots as mod  # noqa: PLC0415

        assert hasattr(mod, "SCREENSHOTS")
        assert hasattr(mod, "main")

    def test_screenshots_has_five_entries(self) -> None:
        """SCREENSHOTS list contains exactly 5 entries."""
        from scripts.capture_screenshots import SCREENSHOTS  # noqa: PLC0415

        assert len(SCREENSHOTS) == 5

    def test_output_paths_under_docs_demo_screenshots(self) -> None:
        """Every screenshot filename starts with a numeric prefix and ends with .png."""
        from scripts.capture_screenshots import SCREENSHOTS  # noqa: PLC0415

        for filename, _, _ in SCREENSHOTS:
            assert filename.endswith(".png")
            prefix = filename.split("_")[0]
            assert prefix.isdigit(), f"Expected numeric prefix, got {prefix!r}"

    def test_graceful_exit_when_playwright_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main() prints install hint and exits with code 1 when playwright is absent."""
        import scripts.capture_screenshots as mod  # noqa: PLC0415

        # Remove playwright from sys.modules so the lazy import actually runs
        _playwright_keys = [k for k in sys.modules if "playwright" in k]
        for _k in _playwright_keys:
            monkeypatch.delitem(sys.modules, _k, raising=False)

        original_import = builtins.__import__

        def mock_import(
            name: str, *args: object, **kwargs: object
        ) -> object:
            if "playwright" in name:
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        with pytest.raises(SystemExit) as exc_info:
            mod.main()
        assert exc_info.value.code == 1

    def test_all_entries_have_expected_types(self) -> None:
        """Each SCREENSHOTS entry is a 3-tuple of correct types."""
        from scripts.capture_screenshots import SCREENSHOTS  # noqa: PLC0415

        for filename, tab_label, query in SCREENSHOTS:
            assert isinstance(filename, str)
            assert isinstance(tab_label, str)
            assert query is None or isinstance(query, str)

    def test_expected_filenames(self) -> None:
        """Check that the expected screenshot filenames are present."""
        from scripts.capture_screenshots import SCREENSHOTS  # noqa: PLC0415

        names = [entry[0] for entry in SCREENSHOTS]
        assert "01_chat_portfolio.png" in names
        assert "02_reasoning_trace.png" in names
        assert "03_trap_refusal.png" in names
        assert "04_digital_twin.png" in names
        assert "05_harness.png" in names
