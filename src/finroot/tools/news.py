"""NewsSearchTool — retrieve financial news articles.

Mock mode returns 3 deterministic canned articles about Indian markets.
Live mode requires ``FINROOT_NEWSAPI_KEY`` env var and calls NewsAPI.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request

from pydantic import BaseModel, Field

from finroot.tools.base import BaseTool, ToolCallError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic models (contract § NewsSearchTool)
# ---------------------------------------------------------------------------


class NewsInput(BaseModel):
    """Input for NewsSearchTool."""

    query: str
    max_results: int = Field(default=5, ge=1, le=20)

    model_config = {"extra": "forbid"}


class NewsArticle(BaseModel):
    """A single news article."""

    title: str
    url: str
    published_at: str
    source: str
    summary: str


class NewsOutput(BaseModel):
    """Output from NewsSearchTool."""

    articles: list[NewsArticle]
    source: str  # "newsapi" | "mock"
    citation: str


# ---------------------------------------------------------------------------
# Mock fixtures
# ---------------------------------------------------------------------------

_MOCK_ARTICLES: list[NewsArticle] = [
    NewsArticle(
        title="Sensex surges 500 points as banking stocks rally",
        url="https://example.com/news/sensex-surges-500",
        published_at="2026-06-19T10:30:00Z",
        source="Mock Financial Times",
        summary=(
            "Indian equity markets rallied sharply on Thursday with the Sensex "
            "gaining over 500 points led by strong buying in banking and financial "
            "stocks. HDFC Bank and ICICI Bank were among the top gainers."
        ),
    ),
    NewsArticle(
        title="RBI holds repo rate steady at 6.5% amid inflation concerns",
        url="https://example.com/news/rbi-holds-rate",
        published_at="2026-06-19T08:00:00Z",
        source="Mock Economic Times",
        summary=(
            "The Reserve Bank of India kept the repo rate unchanged at 6.5% in "
            "its latest monetary policy review, citing persistent inflation above "
            "the 4% target. Governor noted global uncertainty as a key factor."
        ),
    ),
    NewsArticle(
        title="Nifty IT index falls 2% on weak global cues",
        url="https://example.com/news/nifty-it-falls",
        published_at="2026-06-19T12:15:00Z",
        source="Mock Moneycontrol",
        summary=(
            "The Nifty IT index declined over 2% dragged by losses in Infosys "
            "and TCS after weak earnings guidance from US tech majors raised "
            "concerns about demand slowdown in the IT sector."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class NewsSearchTool(BaseTool[NewsInput, NewsOutput]):
    """Retrieve financial news articles from NewsAPI (live) or canned fixtures (mock)."""

    name = "news_search"
    ttl_seconds = 300

    def __init__(self, *, mock: bool = False, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._mock = mock

    def _run(self, inp: NewsInput) -> NewsOutput:
        if self._mock or os.environ.get("FINROOT_LLM_PROVIDER") == "mock":
            return self._run_mock(inp)
        return self._run_live(inp)

    def _run_mock(self, inp: NewsInput) -> NewsOutput:
        articles = _MOCK_ARTICLES[: min(inp.max_results, len(_MOCK_ARTICLES))]
        return NewsOutput(
            articles=articles,
            source="mock",
            citation="Mock news feed",
        )

    def _run_live(self, inp: NewsInput) -> NewsOutput:
        api_key = os.environ.get("FINROOT_NEWSAPI_KEY")
        if not api_key:
            raise ToolCallError(
                "NewsSearchTool requires FINROOT_NEWSAPI_KEY env var for live mode. "
                "Set it or use mock=True / FINROOT_LLM_PROVIDER=mock."
            )

        url = (
            "https://newsapi.org/v2/everything?"
            f"q={inp.query}&language=en&sortBy=publishedAt"
            f"&pageSize={inp.max_results}&apiKey={api_key}"
        )

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FinRoot/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise ToolCallError(f"NewsAPI request failed: {exc}") from exc

        raw_articles = data.get("articles", [])
        articles: list[NewsArticle] = []
        for raw in raw_articles[: inp.max_results]:
            articles.append(
                NewsArticle(
                    title=raw.get("title", ""),
                    url=raw.get("url", ""),
                    published_at=raw.get("publishedAt", ""),
                    source=raw.get("source", {}).get("name", "Unknown"),
                    summary=raw.get("description", "") or "",
                )
            )

        return NewsOutput(
            articles=articles,
            source="newsapi",
            citation=f"NewsAPI, {len(articles)} articles for '{inp.query}'",
        )


__all__ = ["NewsSearchTool", "NewsInput", "NewsArticle", "NewsOutput"]
