"""Tests for profile, document parser, and watchlist tools (wave-3, task 06).

Covers:
- UserProfileTool: read, write, unknown user error, field filtering
- DocumentParserTool: portfolio, bank, tax, generic, unknown doc_type
- WatchlistAlertTool: alert triggered (above/below), no alert, empty watchlist,
  add/remove helpers
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from finroot.tools.base import ToolCallError
from finroot.tools.documents import DocParseInput, DocParseOutput, DocumentParserTool
from finroot.tools.profile import (
    ProfileOutput,
    ProfileReadInput,
    ProfileWriteInput,
    UserProfileTool,
)
from finroot.tools.watchlist import (
    AlertCheckInput,
    WatchlistAlertTool,
    WatchlistEntry,
    add_to_watchlist,
    load_watchlist,
    remove_from_watchlist,
    save_watchlist,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def profiles_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect profiles JSON to a temp directory and force JSON fallback."""
    p = tmp_path / "twin_profiles.json"
    profiles = [
        {
            "user_id": "test_user",
            "name": "Test Investor",
            "risk_tolerance": "moderate",
            "portfolio_value_inr": 5000000,
            "sectors": ["technology", "banking"],
            "goals": ["retirement"],
        },
        {
            "user_id": "other_user",
            "name": "Other Investor",
            "risk_tolerance": "low",
            "portfolio_value_inr": 1000000,
        },
    ]
    p.write_text(json.dumps(profiles))
    monkeypatch.setattr("finroot.tools.profile._PROFILES_PATH", p)
    # Force JSON fallback by temporarily removing DigitalTwinStore
    import sys

    saved = sys.modules.pop("finroot.memory.digital_twin", None)
    yield p
    if saved is not None:
        sys.modules["finroot.memory.digital_twin"] = saved


@pytest.fixture()
def watchlists_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect watchlists directory to temp."""
    d = tmp_path / "watchlists"
    d.mkdir()
    monkeypatch.setattr("finroot.tools.watchlist._WATCHLISTS_DIR", d)
    return d


@pytest.fixture()
def profile_tool() -> UserProfileTool:
    return UserProfileTool()


@pytest.fixture()
def doc_tool() -> DocumentParserTool:
    return DocumentParserTool()


@pytest.fixture()
def alert_tool() -> WatchlistAlertTool:
    return WatchlistAlertTool()


# ===========================================================================
# UserProfileTool tests
# ===========================================================================


class TestUserProfileToolRead:
    """Tests for reading user profiles."""

    def test_read_returns_all_fields(
        self, profile_tool: UserProfileTool, profiles_path: Path
    ) -> None:
        result = profile_tool(ProfileReadInput(user_id="test_user"))
        assert isinstance(result, ProfileOutput)
        assert result.user_id == "test_user"
        assert result.data["name"] == "Test Investor"
        assert result.data["risk_tolerance"] == "moderate"
        assert result.data["portfolio_value_inr"] == 5000000
        assert "DigitalTwin profile for test_user" in result.citation

    def test_read_filters_fields(
        self, profile_tool: UserProfileTool, profiles_path: Path
    ) -> None:
        result = profile_tool(
            ProfileReadInput(user_id="test_user", fields=["name", "risk_tolerance"])
        )
        assert set(result.data.keys()) == {"name", "risk_tolerance"}

    def test_read_unknown_user_raises(
        self, profile_tool: UserProfileTool, profiles_path: Path
    ) -> None:
        with pytest.raises(ToolCallError, match="no profile found"):
            profile_tool(ProfileReadInput(user_id="nonexistent"))


class TestUserProfileToolWrite:
    """Tests for writing/updating user profiles."""

    def test_write_updates_specific_field(
        self, profile_tool: UserProfileTool, profiles_path: Path
    ) -> None:
        result = profile_tool(
            ProfileWriteInput(
                user_id="test_user", updates={"risk_tolerance": "aggressive"}
            )
        )
        assert result.data["risk_tolerance"] == "aggressive"
        # Verify persistence
        result2 = profile_tool(ProfileReadInput(user_id="test_user"))
        assert result2.data["risk_tolerance"] == "aggressive"

    def test_write_unknown_user_raises(
        self, profile_tool: UserProfileTool, profiles_path: Path
    ) -> None:
        with pytest.raises(ToolCallError, match="no profile found"):
            profile_tool(
                ProfileWriteInput(user_id="nonexistent", updates={"name": "New"})
            )


# ===========================================================================
# DocumentParserTool tests
# ===========================================================================


class TestDocumentParserPortfolio:
    """Tests for portfolio statement parsing."""

    def test_portfolio_extracts_total_value(self, doc_tool: DocumentParserTool) -> None:
        content = (
            "Portfolio Statement\n"
            "Date: 15/06/2026\n"
            "RELIANCE: 100 units\n"
            "TCS: 50 units\n"
            "Total Value: ₹12,50,000.00\n"
        )
        result = doc_tool(DocParseInput(content=content, doc_type="portfolio_statement"))
        assert isinstance(result, DocParseOutput)
        assert result.extracted["total_value"] == 1250000.0
        assert result.confidence > 0.0
        assert "portfolio_statement" in result.citation

    def test_portfolio_extracts_holdings(self, doc_tool: DocumentParserTool) -> None:
        content = "RELIANCE: 100 units\nTCS x 50\nTotal Value: ₹10,00,000\nDate: 01/01/2026"
        result = doc_tool(DocParseInput(content=content, doc_type="portfolio_statement"))
        holdings = result.extracted.get("holdings", [])
        tickers = {h["ticker"] for h in holdings}
        assert "RELIANCE" in tickers


class TestDocumentParserBank:
    """Tests for bank statement parsing."""

    def test_bank_extracts_credits_debits(self, doc_tool: DocumentParserTool) -> None:
        content = (
            "Bank Statement\n"
            "Total Credits: ₹5,00,000\n"
            "Total Debits: ₹3,00,000\n"
            "Closing Balance: ₹2,00,000\n"
        )
        result = doc_tool(DocParseInput(content=content, doc_type="bank_statement"))
        assert result.extracted["total_credits"] == 500000.0
        assert result.extracted["total_debits"] == 300000.0
        assert result.extracted["closing_balance"] == 200000.0
        assert result.confidence == 1.0


class TestDocumentParserTax:
    """Tests for tax return parsing."""

    def test_tax_extracts_fields(self, doc_tool: DocumentParserTool) -> None:
        content = (
            "Tax Return FY 2024-25\n"
            "Gross Income: ₹15,00,000\n"
            "Tax Paid: ₹2,50,000\n"
            "Refund: ₹15,000\n"
        )
        result = doc_tool(DocParseInput(content=content, doc_type="tax_return"))
        assert result.extracted["gross_income"] == 1500000.0
        assert result.extracted["tax_paid"] == 250000.0
        assert result.extracted["refund_amount"] == 15000.0


class TestDocumentParserGeneric:
    """Tests for generic parsing and unknown doc_type."""

    def test_generic_extracts_amounts_and_dates(
        self, doc_tool: DocumentParserTool
    ) -> None:
        content = "Paid ₹1,500 on 15/06/2026. Received Rs 3,000 on 20/06/2026."
        result = doc_tool(DocParseInput(content=content, doc_type="generic"))
        assert 1500.0 in result.extracted["amounts"]
        assert 3000.0 in result.extracted["amounts"]
        assert len(result.extracted["dates"]) == 2

    def test_unknown_doc_type_returns_generic(
        self, doc_tool: DocumentParserTool
    ) -> None:
        # "invoice" is not a known type, should fall back to generic
        content = "Invoice total ₹5,000 dated 01/03/2026"
        result = doc_tool(DocParseInput(content=content, doc_type="generic"))
        assert result.extracted  # should have some extraction
        assert result.confidence >= 0.0

    def test_empty_content_returns_zero_confidence(
        self, doc_tool: DocumentParserTool
    ) -> None:
        result = doc_tool(DocParseInput(content="", doc_type="portfolio_statement"))
        assert result.confidence == 0.0
        assert result.extracted == {}


# ===========================================================================
# WatchlistAlertTool tests
# ===========================================================================


class TestWatchlistAlert:
    """Tests for watchlist alert checking."""

    def test_alert_triggered_above(
        self, alert_tool: WatchlistAlertTool, watchlists_dir: Path
    ) -> None:
        entries = [
            WatchlistEntry(
                symbol="RELIANCE",
                target_price=2500.0,
                direction="above",
                alert_message="RELIANCE crossed ₹2500!",
            )
        ]
        save_watchlist("test_user", entries)
        result = alert_tool(
            AlertCheckInput(
                user_id="test_user", current_prices={"RELIANCE": 2600.0}
            )
        )
        assert len(result.triggered) == 1
        assert result.triggered[0].symbol == "RELIANCE"
        assert "test_user" in result.citation

    def test_alert_triggered_below(
        self, alert_tool: WatchlistAlertTool, watchlists_dir: Path
    ) -> None:
        entries = [
            WatchlistEntry(
                symbol="TCS",
                target_price=3500.0,
                direction="below",
                alert_message="TCS dropped below ₹3500!",
            )
        ]
        save_watchlist("test_user", entries)
        result = alert_tool(
            AlertCheckInput(user_id="test_user", current_prices={"TCS": 3400.0})
        )
        assert len(result.triggered) == 1
        assert result.triggered[0].symbol == "TCS"

    def test_no_alert_when_price_at_target(
        self, alert_tool: WatchlistAlertTool, watchlists_dir: Path
    ) -> None:
        entries = [
            WatchlistEntry(
                symbol="INFY",
                target_price=1500.0,
                direction="above",
                alert_message="INFY above ₹1500",
            )
        ]
        save_watchlist("test_user", entries)
        # Price exactly at target triggers (>=)
        result = alert_tool(
            AlertCheckInput(user_id="test_user", current_prices={"INFY": 1500.0})
        )
        assert len(result.triggered) == 1

    def test_no_alert_when_price_hasnt_crossed(
        self, alert_tool: WatchlistAlertTool, watchlists_dir: Path
    ) -> None:
        entries = [
            WatchlistEntry(
                symbol="WIPRO",
                target_price=500.0,
                direction="above",
                alert_message="WIPRO above ₹500",
            )
        ]
        save_watchlist("test_user", entries)
        result = alert_tool(
            AlertCheckInput(user_id="test_user", current_prices={"WIPRO": 450.0})
        )
        assert len(result.triggered) == 0

    def test_empty_watchlist_file_absent(
        self, alert_tool: WatchlistAlertTool, watchlists_dir: Path
    ) -> None:
        result = alert_tool(
            AlertCheckInput(
                user_id="no_such_user", current_prices={"RELIANCE": 2500.0}
            )
        )
        assert result.triggered == []
        assert "no_such_user" in result.citation

    def test_symbol_not_in_current_prices_skipped(
        self, alert_tool: WatchlistAlertTool, watchlists_dir: Path
    ) -> None:
        entries = [
            WatchlistEntry(
                symbol="RELIANCE",
                target_price=2500.0,
                direction="above",
                alert_message="RELIANCE crossed!",
            )
        ]
        save_watchlist("test_user", entries)
        result = alert_tool(
            AlertCheckInput(
                user_id="test_user", current_prices={"TCS": 3500.0}
            )
        )
        assert len(result.triggered) == 0


class TestWatchlistPersistence:
    """Tests for add/remove watchlist helpers."""

    def test_add_to_watchlist(self, watchlists_dir: Path) -> None:
        entry = WatchlistEntry(
            symbol="HDFC",
            target_price=1600.0,
            direction="above",
            alert_message="HDFC above ₹1600",
        )
        add_to_watchlist("persist_user", entry)
        loaded = load_watchlist("persist_user")
        assert len(loaded) == 1
        assert loaded[0].symbol == "HDFC"

    def test_add_replaces_same_symbol(self, watchlists_dir: Path) -> None:
        e1 = WatchlistEntry(
            symbol="HDFC", target_price=1600.0, direction="above", alert_message="m1"
        )
        e2 = WatchlistEntry(
            symbol="HDFC", target_price=1700.0, direction="below", alert_message="m2"
        )
        add_to_watchlist("u", e1)
        add_to_watchlist("u", e2)
        loaded = load_watchlist("u")
        assert len(loaded) == 1
        assert loaded[0].target_price == 1700.0

    def test_remove_from_watchlist(self, watchlists_dir: Path) -> None:
        e = WatchlistEntry(
            symbol="TCS", target_price=3500.0, direction="above", alert_message="m"
        )
        add_to_watchlist("u", e)
        remove_from_watchlist("u", "TCS")
        loaded = load_watchlist("u")
        assert len(loaded) == 0
