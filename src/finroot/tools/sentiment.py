"""SentimentAnalysisTool — financial sentiment analysis.

Heuristic baseline (always available): keyword lists for positive/negative
financial terms with score = (pos - neg) / total_words, clipped to [-1, 1].

FinBERT path: lazy import ``transformers``; if available and
``FINROOT_SENTIMENT_MODEL=finbert`` → use ``ProsusAI/finbert``.
Falls back to heuristic with a ``logger.warning`` (FM-11).
"""

from __future__ import annotations

import logging
import os
from typing import Literal

from pydantic import BaseModel, Field

from finroot.tools.base import BaseTool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic models (contract § SentimentAnalysisTool)
# ---------------------------------------------------------------------------


class SentimentInput(BaseModel):
    """Input for SentimentAnalysisTool."""

    texts: list[str] = Field(min_length=1, max_length=20)

    model_config = {"extra": "forbid"}


class SentimentResult(BaseModel):
    """Sentiment for a single text."""

    text: str
    label: Literal["positive", "negative", "neutral"]
    score: float


class SentimentOutput(BaseModel):
    """Output from SentimentAnalysisTool."""

    results: list[SentimentResult]
    model: str  # "heuristic" | "finbert"
    citation: str


# ---------------------------------------------------------------------------
# Heuristic keyword lists
# ---------------------------------------------------------------------------

_POSITIVE_KEYWORDS: set[str] = {
    "surge", "rally", "gain", "profit", "bullish", "upgrade", "outperform",
    "beat", "growth", "record", "high", "strong", "optimistic", "positive",
    "rise", "soar", "jump", "boom", "recovery", "uptrend", "breakout",
    "dividend", "buyback", "expansion", "innovation", "efficient",
}

_NEGATIVE_KEYWORDS: set[str] = {
    "crash", "plunge", "loss", "bearish", "downgrade", "underperform",
    "miss", "decline", "low", "weak", "pessimistic", "negative", "fall",
    "drop", "slump", "recession", "bankruptcy", "default", "risk",
    "sell-off", "selloff", "panic", "crisis", "debt", "inflation",
}


# ---------------------------------------------------------------------------
# Heuristic implementation
# ---------------------------------------------------------------------------


def _heuristic_score(text: str) -> tuple[str, float]:
    """Compute sentiment using keyword matching.

    Returns (label, score) where score is clipped to [-1, 1].
    """
    words = text.lower().split()
    if not words:
        return "neutral", 0.0

    pos_count = sum(1 for w in words if w in _POSITIVE_KEYWORDS)
    neg_count = sum(1 for w in words if w in _NEGATIVE_KEYWORDS)
    total = len(words)

    raw = (pos_count - neg_count) / total
    score = max(-1.0, min(1.0, raw))

    if score > 0.05:
        label = "positive"
    elif score < -0.05:
        label = "negative"
    else:
        label = "neutral"

    return label, round(score, 4)


# ---------------------------------------------------------------------------
# FinBERT path (lazy import)
# ---------------------------------------------------------------------------

_finbert_pipeline = None


def _get_finbert_pipeline():  # type: ignore[no-untyped-def]
    """Lazily load FinBERT pipeline. Returns None if transformers unavailable."""
    global _finbert_pipeline
    if _finbert_pipeline is not None:
        return _finbert_pipeline

    try:
        from transformers import pipeline  # type: ignore[import-untyped]
    except ImportError:
        logger.warning(
            "transformers package not available; falling back to heuristic sentiment."
        )
        return None

    try:
        _finbert_pipeline = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            top_k=None,
        )
        return _finbert_pipeline
    except Exception as exc:
        logger.warning("Failed to load FinBERT model: %s; using heuristic.", exc)
        return None


def _finbert_score(text: str, pipe) -> tuple[str, float]:  # type: ignore[no-untyped-def]
    """Score a single text using FinBERT pipeline."""
    result = pipe(text[:512])  # FinBERT max length
    if isinstance(result, list) and len(result) > 0:
        scores = {r["label"]: r["score"] for r in result[0]}
        pos = scores.get("positive", 0.0)
        neg = scores.get("negative", 0.0)
        score = max(-1.0, min(1.0, pos - neg))
        if score > 0.05:
            label = "positive"
        elif score < -0.05:
            label = "negative"
        else:
            label = "neutral"
        return label, round(score, 4)
    return "neutral", 0.0


# ---------------------------------------------------------------------------
# Tool
# ---------------------------------------------------------------------------


class SentimentAnalysisTool(BaseTool[SentimentInput, SentimentOutput]):
    """Analyze sentiment of financial texts using heuristic or FinBERT."""

    name = "sentiment_analysis"
    ttl_seconds = 300

    def __init__(self, *, mock: bool = False, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._mock = mock
        self._use_finbert = False

        # Determine which model to use
        model_env = os.environ.get("FINROOT_SENTIMENT_MODEL", "")
        if model_env == "finbert" and not mock:
            pipe = _get_finbert_pipeline()
            if pipe is not None:
                self._use_finbert = True
                self._finbert_pipe = pipe
            else:
                logger.warning(
                    "FinBERT requested via FINROOT_SENTIMENT_MODEL=finbert but "
                    "could not be loaded; using heuristic fallback."
                )

    def _run(self, inp: SentimentInput) -> SentimentOutput:
        results: list[SentimentResult] = []

        for text in inp.texts:
            if not text or not text.strip():
                results.append(
                    SentimentResult(text=text, label="neutral", score=0.0)
                )
                continue

            if self._use_finbert:
                label, score = _finbert_score(text, self._finbert_pipe)
            else:
                label, score = _heuristic_score(text)

            results.append(SentimentResult(text=text, label=label, score=score))

        model_name = "finbert" if self._use_finbert else "heuristic"
        return SentimentOutput(
            results=results,
            model=model_name,
            citation=f"FinRoot sentiment ({model_name} model)",
        )


__all__ = ["SentimentAnalysisTool", "SentimentInput", "SentimentResult", "SentimentOutput"]
