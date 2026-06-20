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

_MOCK_ARTICLES_BY_TOPIC: dict[str, list[NewsArticle]] = {
    "market": [
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
    ],
    "rbi": [
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
            title="RBI announces new digital lending guidelines for NBFCs",
            url="https://example.com/news/rbi-digital-lending",
            published_at="2026-06-18T14:00:00Z",
            source="Mock Business Standard",
            summary=(
                "The Reserve Bank of India issued updated digital lending guidelines "
                "requiring NBFCs to disclose all fees upfront and provide a cooling-off "
                "period for borrowers. The move aims to curb predatory lending practices."
            ),
        ),
    ],
    "tax": [
        NewsArticle(
            title="Budget 2025: New tax regime becomes default, old regime benefits reviewed",
            url="https://example.com/news/budget-2025-tax",
            published_at="2026-02-01T10:00:00Z",
            source="Mock Economic Times",
            summary=(
                "Finance Minister announced the new tax regime as the default option "
                "with revised slabs. Standard deduction increased to ₹75,000. "
                "Taxpayers can still opt for the old regime with deductions."
            ),
        ),
        NewsArticle(
            title="CBDT extends ITR filing deadline for AY 2025-26",
            url="https://example.com/news/itr-deadline-extended",
            published_at="2026-07-15T09:00:00Z",
            source="Mock Moneycontrol",
            summary=(
                "The Central Board of Direct Taxes extended the income tax return "
                "filing deadline to September 30 for assessment year 2025-26, "
                "citing technical issues on the e-filing portal."
            ),
        ),
    ],
    "stock": [
        NewsArticle(
            title="Reliance Industries reports record quarterly profit of ₹19,000 crore",
            url="https://example.com/news/reliance-record-profit",
            published_at="2026-06-18T16:00:00Z",
            source="Mock Mint",
            summary=(
                "Reliance Industries posted a record consolidated net profit of "
                "₹19,000 crore in Q1 FY26, driven by strong performance in "
                "digital services and retail segments. O2C margins improved."
            ),
        ),
        NewsArticle(
            title="TCS announces ₹18,000 crore buyback, stock hits 52-week high",
            url="https://example.com/news/tcs-buyback",
            published_at="2026-06-17T11:00:00Z",
            source="Mock Financial Express",
            summary=(
                "Tata Consultancy Services approved a ₹18,000 crore share buyback "
                "at ₹4,500 per share. The stock hit a 52-week high following the "
                "announcement. Analysts see it as a sign of management confidence."
            ),
        ),
    ],
    "mutual_fund": [
        NewsArticle(
            title="SBI Mutual Fund launches new flexi-cap fund, NFO opens next week",
            url="https://example.com/news/sbi-flexi-cap-nfo",
            published_at="2026-06-19T09:00:00Z",
            source="Mock Moneycontrol",
            summary=(
                "SBI Mutual Fund launched a new flexi-cap fund targeting long-term "
                "capital appreciation across market capitalizations. The NFO opens "
                "on June 25 with minimum investment of ₹5,000."
            ),
        ),
        NewsArticle(
            title="ELSS funds deliver 22% average returns over 3 years",
            url="https://example.com/news/elss-returns",
            published_at="2026-06-16T10:00:00Z",
            source="Mock ET Markets",
            summary=(
                "Equity Linked Savings Scheme funds delivered an average 3-year "
                "return of 22%, outperforming large-cap funds. Top performers "
                "include Mirae Asset Tax Saver and Canara Robeco Equity Tax Saver."
            ),
        ),
    ],
    "insurance": [
        NewsArticle(
            title="IRDAI increases health insurance portability window to 60 days",
            url="https://example.com/news/irdai-portability",
            published_at="2026-06-15T12:00:00Z",
            source="Mock Business Standard",
            summary=(
                "Insurance Regulatory and Development Authority of India extended "
                "the health insurance portability request window from 45 to 60 days "
                "before policy renewal, giving policyholders more time to switch."
            ),
        ),
        NewsArticle(
            title="Term insurance premiums rise 15% as reinsurers increase rates",
            url="https://example.com/news/term-insurance-premium-hike",
            published_at="2026-06-14T08:00:00Z",
            source="Mock Mint",
            summary=(
                "Term insurance premiums are set to rise 15% as global reinsurers "
                "increased rates for Indian insurers. Industry experts recommend "
                "buying term plans before the new rates take effect in July."
            ),
        ),
    ],
    "default": [
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
    ],
}


def _select_mock_articles(query: str, max_results: int) -> list[NewsArticle]:
    """Select mock articles based on query keywords."""
    query_lower = query.lower()
    topic_keywords = {
        "rbi": ["rbi", "repo", "rate", "monetary", "inflation", "interest rate"],
        "tax": ["tax", "itr", "budget", "capital gains", "80c", "deduction", "cess"],
        "stock": ["reliance", "tcs", "infosys", "stock", "share", "equity", "nifty", "sensex", "buyback"],
        "mutual_fund": ["mutual fund", "sip", "elss", "nfo", "nav", "scheme", "amc"],
        "insurance": ["insurance", "irdai", "term", "health", "premium", "claim"],
        "market": ["market", "rally", "index", "trading", "bull", "bear"],
    }
    for topic, keywords in topic_keywords.items():
        if any(kw in query_lower for kw in keywords):
            articles = _MOCK_ARTICLES_BY_TOPIC.get(topic, _MOCK_ARTICLES_BY_TOPIC["default"])
            return articles[:min(max_results, len(articles))]
    articles = _MOCK_ARTICLES_BY_TOPIC["default"]
    return articles[:min(max_results, len(articles))]


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
        articles = _select_mock_articles(inp.query, inp.max_results)
        return NewsOutput(
            articles=articles,
            source="mock",
            citation=f"Mock news feed for '{inp.query}'",
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
