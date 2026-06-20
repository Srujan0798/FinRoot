"""Tests for NewsSearchTool and SentimentAnalysisTool (wave-3 task 02)."""

from __future__ import annotations

import os

import pytest
from pydantic import ValidationError

from finroot.tools.base import ToolCallError
from finroot.tools.news import NewsArticle, NewsInput, NewsOutput, NewsSearchTool
from finroot.tools.sentiment import (
    SentimentAnalysisTool,
    SentimentInput,
)

# =========================================================================
# NewsSearchTool tests
# =========================================================================


class TestNewsSearchToolMock:
    """Tests for NewsSearchTool in mock mode."""

    def test_mock_returns_articles(self) -> None:
        tool = NewsSearchTool(mock=True)
        result = tool(NewsInput(query="indian markets"))
        assert isinstance(result, NewsOutput)
        assert len(result.articles) >= 2  # Topic-based: market has 2 articles

    def test_mock_article_shape(self) -> None:
        tool = NewsSearchTool(mock=True)
        result = tool(NewsInput(query="test"))
        for article in result.articles:
            assert isinstance(article, NewsArticle)
            assert article.title
            assert article.url.startswith("https://")
            assert article.published_at
            assert article.source
            assert article.summary

    def test_mock_source_and_citation(self) -> None:
        tool = NewsSearchTool(mock=True)
        result = tool(NewsInput(query="test"))
        assert result.source == "mock"
        assert result.citation == "Mock news feed for 'test'"

    def test_mock_respects_max_results(self) -> None:
        tool = NewsSearchTool(mock=True)
        result = tool(NewsInput(query="test", max_results=1))
        assert len(result.articles) == 1

    def test_max_results_validation_too_low(self) -> None:
        with pytest.raises(ValidationError):
            NewsInput(query="test", max_results=0)

    def test_max_results_validation_too_high(self) -> None:
        with pytest.raises(ValidationError):
            NewsInput(query="test", max_results=21)


@pytest.mark.skipif(
    os.environ.get("FINROOT_LLM_PROVIDER", "").lower() == "mock",
    reason="Live tests skipped in mock mode",
)
class TestNewsSearchToolLive:
    """Tests for NewsSearchTool in live mode."""

    def test_live_raises_without_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("FINROOT_NEWSAPI_KEY", raising=False)
        tool = NewsSearchTool(mock=False)
        with pytest.raises(ToolCallError, match="FINROOT_NEWSAPI_KEY"):
            tool(NewsInput(query="test"))

    def test_mock_env_provider(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FINROOT_LLM_PROVIDER", "mock")
        tool = NewsSearchTool(mock=False)
        result = tool(NewsInput(query="test"))
        assert result.source == "mock"


# =========================================================================
# SentimentAnalysisTool tests
# =========================================================================


class TestSentimentAnalysisToolHeuristic:
    """Tests for SentimentAnalysisTool with heuristic model."""

    def test_positive_sentiment(self) -> None:
        tool = SentimentAnalysisTool(mock=True)
        result = tool(SentimentInput(texts=["market surge rally growth profit"]))
        assert len(result.results) == 1
        assert result.results[0].label == "positive"
        assert result.results[0].score > 0

    def test_negative_sentiment(self) -> None:
        tool = SentimentAnalysisTool(mock=True)
        result = tool(SentimentInput(texts=["bankruptcy crash plunge loss"]))
        assert len(result.results) == 1
        assert result.results[0].label == "negative"
        assert result.results[0].score < 0

    def test_neutral_sentiment(self) -> None:
        tool = SentimentAnalysisTool(mock=True)
        result = tool(SentimentInput(texts=["stable market conditions remain"]))
        assert len(result.results) == 1
        assert result.results[0].label == "neutral"

    def test_empty_text_graceful(self) -> None:
        tool = SentimentAnalysisTool(mock=True)
        result = tool(SentimentInput(texts=[""]))
        assert len(result.results) == 1
        assert result.results[0].label == "neutral"
        assert result.results[0].score == 0.0

    def test_whitespace_only_text(self) -> None:
        tool = SentimentAnalysisTool(mock=True)
        result = tool(SentimentInput(texts=["   "]))
        assert len(result.results) == 1
        assert result.results[0].label == "neutral"
        assert result.results[0].score == 0.0

    def test_multiple_texts(self) -> None:
        tool = SentimentAnalysisTool(mock=True)
        result = tool(
            SentimentInput(
                texts=["surge rally profit", "crash bankruptcy", "stable market"]
            )
        )
        assert len(result.results) == 3
        assert result.results[0].label == "positive"
        assert result.results[1].label == "negative"
        assert result.results[2].label == "neutral"

    def test_model_name_heuristic(self) -> None:
        tool = SentimentAnalysisTool(mock=True)
        result = tool(SentimentInput(texts=["test"]))
        assert result.model == "heuristic"

    def test_citation_present(self) -> None:
        tool = SentimentAnalysisTool(mock=True)
        result = tool(SentimentInput(texts=["test"]))
        assert "heuristic" in result.citation


class TestSentimentAnalysisToolFinBERT:
    """Tests for SentimentAnalysisTool FinBERT path."""

    def test_finbert_skipped_when_transformers_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """FinBERT path falls back to heuristic when transformers not importable."""
        monkeypatch.setenv("FINROOT_SENTIMENT_MODEL", "finbert")
        # Simulate transformers not being available by patching the import
        import finroot.tools.sentiment as mod

        original_get = mod._get_finbert_pipeline
        mod._get_finbert_pipeline = lambda: None
        try:
            tool = SentimentAnalysisTool(mock=False)
            result = tool(SentimentInput(texts=["test"]))
            assert result.model == "heuristic"
        finally:
            mod._get_finbert_pipeline = original_get


class TestSentimentPydanticValidation:
    """Tests for SentimentInput validation."""

    def test_empty_texts_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SentimentInput(texts=[])

    def test_too_many_texts_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SentimentInput(texts=["t"] * 21)

    def test_score_clipping(self) -> None:
        tool = SentimentAnalysisTool(mock=True)
        # Text with many positive keywords should clip to 1.0
        result = tool(
            SentimentInput(
                texts=["surge rally gain profit bullish upgrade outperform beat growth record high strong"]
            )
        )
        assert result.results[0].score <= 1.0
        assert result.results[0].score >= -1.0
