"""Security tests — input validation (wave-11, task 04).

Verifies that the system handles adversarial and malformed inputs gracefully
without crashes, data leaks, or silent corruption. Every test uses the
``@pytest.mark.security`` marker.

Covers
------
* Empty query handling
* Very long query (>10 000 chars)
* SQL injection attempts in query
* Script (XSS) injection attempts in query
* Special characters: unicode, emojis, null bytes
* Invalid tool output format
* Invalid recommendation format
* Invalid audit event format
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from finroot.agents.intent import IntentClassifier
from finroot.schemas.audit import AuditEvent
from finroot.schemas.enums import ConfidenceLevel, Intent
from finroot.schemas.recommendation import Citation, Recommendation
from finroot.schemas.state import AgentState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

UTC_NOW = datetime(2026, 6, 19, 12, 0, 0, tzinfo=UTC)
ZERO_HASH = "0" * 64
SAMPLE_HASH = "a" * 64


def _valid_citation() -> Citation:
    return Citation(
        source="yfinance",
        detail="AAPL last close",
        value="150.25",
        retrieved_at=UTC_NOW,
    )


def _valid_recommendation(**overrides) -> Recommendation:
    defaults = {
        "summary": "Buy AAPL",
        "analysis": "The stock trades at 150.25 which is fair.",
        "confidence": ConfidenceLevel.MEDIUM,
        "citations": [_valid_citation()],
    }
    defaults.update(overrides)
    return Recommendation(**defaults)


def _valid_audit_event(**overrides) -> AuditEvent:
    defaults = {
        "ts": UTC_NOW,
        "seq": 0,
        "type": "task.dispatched",
        "payload": {"task_id": "01"},
        "prev_hash": ZERO_HASH,
        "hash": SAMPLE_HASH,
    }
    defaults.update(overrides)
    return AuditEvent(**defaults)


# ---------------------------------------------------------------------------
# 1. Empty query handled gracefully
# ---------------------------------------------------------------------------


@pytest.mark.security
class TestEmptyQuery:
    def test_empty_string_classified_as_general(self) -> None:
        clf = IntentClassifier()
        result = clf.classify("")
        assert result.intent == Intent.GENERAL

    def test_whitespace_only_query(self) -> None:
        clf = IntentClassifier()
        result = clf.classify("   \t\n  ")
        assert result.intent == Intent.GENERAL

    def test_empty_query_entities(self) -> None:
        clf = IntentClassifier()
        result = clf.classify("")
        assert result.entities == {"symbols": [], "timeframe": None}


# ---------------------------------------------------------------------------
# 2. Very long query (>10 000 chars) handled gracefully
# ---------------------------------------------------------------------------


@pytest.mark.security
class TestVeryLongQuery:
    def test_long_query_does_not_crash(self) -> None:
        clf = IntentClassifier()
        long_query = "stock " * 5000  # ~30 000 chars
        result = clf.classify(long_query)
        assert isinstance(result.intent, Intent)

    def test_long_query_returns_entity_extraction(self) -> None:
        clf = IntentClassifier()
        long_query = "What is the price of AAPL? " * 1000
        result = clf.classify(long_query)
        assert "symbols" in result.entities


# ---------------------------------------------------------------------------
# 3. SQL injection attempt in query
# ---------------------------------------------------------------------------


@pytest.mark.security
class TestSQLInjection:
    SQL_PAYLOADS = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "SELECT * FROM digital_twins WHERE 1=1",
        "'; INSERT INTO users VALUES('admin','pass'); --",
        "UNION SELECT password FROM users--",
        "1; UPDATE users SET role='admin' WHERE 1=1",
    ]

    @pytest.mark.parametrize("payload", SQL_PAYLOADS)
    def test_sql_injection_classified_safely(self, payload: str) -> None:
        clf = IntentClassifier()
        result = clf.classify(payload)
        assert isinstance(result.intent, Intent)

    @pytest.mark.parametrize("payload", SQL_PAYLOADS)
    def test_sql_injection_no_side_effects(self, payload: str) -> None:
        clf = IntentClassifier()
        result = clf.classify(payload)
        # Must not crash; entities should still be well-formed
        assert isinstance(result.entities, dict)
        assert isinstance(result.entities.get("symbols"), list)


# ---------------------------------------------------------------------------
# 4. Script injection attempt in query
# ---------------------------------------------------------------------------


@pytest.mark.security
class TestScriptInjection:
    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        '<img src=x onerror=alert(1)>',
        "<svg/onload=alert('xss')>",
        "javascript:alert(document.cookie)",
        '<body onload=alert("xss")>',
        "{{7*7}}",  # template injection
        "${7*7}",  # expression injection
    ]

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_injection_classified_safely(self, payload: str) -> None:
        clf = IntentClassifier()
        result = clf.classify(payload)
        assert isinstance(result.intent, Intent)

    def test_xss_not_reflected_in_entities(self) -> None:
        clf = IntentClassifier()
        result = clf.classify("<script>alert('xss')</script>")
        # The raw HTML should not appear in extracted entities
        for val in result.entities.values():
            if isinstance(val, str):
                assert "<script>" not in val
            elif isinstance(val, list):
                for item in val:
                    assert "<script>" not in item


# ---------------------------------------------------------------------------
# 5. Special characters in query (unicode, emojis, null bytes)
# ---------------------------------------------------------------------------


@pytest.mark.security
class TestSpecialCharacters:
    UNICODE_PAYLOADS = [
        "What about \u00e9\u00e8\u00ea stocks?",
        "Show me \u4e2d\u56fd stocks",
        "\u0939\u093f\u0928\u094d\u0926\u0940 \u092c\u091c\u0e3e\u0930",
        "Price of \u0410\u041f\u0422\u041b",
    ]

    EMOJI_PAYLOADS = [
        "\U0001f4b0 What about crypto?",
        "Should I \U0001f680 invest?",
        "\U0001f4c9 Is this a \U0001f4c8?",
        "\u2764\ufe0f I love stocks",
    ]

    NULL_PAYLOADS = [
        "stock\x00price",
        "fund\x00amental\x00analysis",
        "\x00\x00\x00",
    ]

    @pytest.mark.parametrize("payload", UNICODE_PAYLOADS)
    def test_unicode_handled(self, payload: str) -> None:
        clf = IntentClassifier()
        result = clf.classify(payload)
        assert isinstance(result.intent, Intent)

    @pytest.mark.parametrize("payload", EMOJI_PAYLOADS)
    def test_emoji_handled(self, payload: str) -> None:
        clf = IntentClassifier()
        result = clf.classify(payload)
        assert isinstance(result.intent, Intent)

    @pytest.mark.parametrize("payload", NULL_PAYLOADS)
    def test_null_bytes_handled(self, payload: str) -> None:
        clf = IntentClassifier()
        result = clf.classify(payload)
        assert isinstance(result.intent, Intent)


# ---------------------------------------------------------------------------
# 6. Invalid tool output format — schemas reject malformed data
# ---------------------------------------------------------------------------


@pytest.mark.security
class TestInvalidToolOutput:
    def test_tool_output_with_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AgentState.model_validate({"query": "test", "fake_field": "should fail"})

    def test_agent_state_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            AgentState.model_validate({"query": "test", "unknown_field": 42})

    def test_agent_state_rejects_wrong_types(self) -> None:
        with pytest.raises(ValidationError):
            AgentState.model_validate({"query": 12345})  # query must be str

    def test_empty_tool_output_list_accepted(self) -> None:
        state = AgentState(query="test", tool_outputs=[])
        assert state.tool_outputs == []


# ---------------------------------------------------------------------------
# 7. Invalid recommendation format
# ---------------------------------------------------------------------------


@pytest.mark.security
class TestInvalidRecommendation:
    def test_empty_summary_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Recommendation(
                summary="",
                analysis="Some analysis",
                confidence=ConfidenceLevel.MEDIUM,
            )

    def test_empty_analysis_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Recommendation(
                summary="Valid summary",
                analysis="",
                confidence=ConfidenceLevel.MEDIUM,
            )

    def test_numeric_analysis_without_citations_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Recommendation(
                summary="Valid summary",
                analysis="The P/E ratio is 25.5 and EPS is 3.2.",
                confidence=ConfidenceLevel.MEDIUM,
                citations=[],
            )

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _valid_recommendation(hacked_field="should fail")

    def test_invalid_confidence_level_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _valid_recommendation(confidence="super_high")


# ---------------------------------------------------------------------------
# 8. Invalid audit event format
# ---------------------------------------------------------------------------


@pytest.mark.security
class TestInvalidAuditEvent:
    def test_empty_type_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _valid_audit_event(type="")

    def test_non_hex_hash_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _valid_audit_event(hash="not_a_hex_string" * 5)

    def test_short_hash_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _valid_audit_event(hash="abc123")

    def test_negative_seq_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _valid_audit_event(seq=-1)

    def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _valid_audit_event(ts=datetime(2026, 1, 1, 0, 0, 0))

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _valid_audit_event(injected_field="malicious")
