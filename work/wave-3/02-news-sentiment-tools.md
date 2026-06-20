# Task wave-3/02 — NewsSearchTool + SentimentAnalysisTool

> Read `work/WORKER_PROMPT.md` then build. Parallel with other wave-3 tasks.

## Objective
Implement news retrieval (NewsAPI with Mock fallback) and financial sentiment analysis
(keyword heuristic baseline + optional FinBERT when `transformers` is available).

## Writes (ONLY these)
- `src/finroot/tools/news.py`
- `src/finroot/tools/sentiment.py`
- `tests/unit/test_tools_news.py`

## Forbid
All other `src/finroot/tools/` files.

## Contract
Read `.specify/specs/wave-3/contracts/tools.contract.md` § NewsSearchTool, § SentimentAnalysisTool.

## Steps
1. `NewsSearchTool(BaseTool)`:
   - Mock mode (default): return 3 canned articles about Indian markets; citation "Mock news feed"
   - Live mode: `FINROOT_NEWSAPI_KEY` env var required; call `https://newsapi.org/v2/everything`. If key absent → `ToolError` (FM-11, not a silent empty list).
   - `max_results` validated (1–20).
   - Cache TTL 300s.

2. `SentimentAnalysisTool(BaseTool)`:
   - Heuristic (always available): keyword lists for positive/negative financial terms; score = (pos - neg) / total_words; clipped to [-1, 1].
   - FinBERT path: lazy import `transformers`; if available and `FINROOT_SENTIMENT_MODEL=finbert` → use `ProsusAI/finbert`. Falls back to heuristic with a `logger.warning` (not silent — FM-11).
   - Input: `texts` list 1–20 items; each item scored independently.
   - Deterministic in Mock mode (heuristic is deterministic).
   - Cache TTL 300s.

3. Tests (minimum 12):
   - News mock returns 3 articles with correct shape
   - News live mode raises `ToolError` when no API key (monkeypatch `os.environ`)
   - Sentiment positive/negative/neutral correct on known strings ("market surge", "bankruptcy", "stable")
   - Sentiment handles empty text gracefully (neutral, score 0.0)
   - max_results validation
   - FinBERT path skipped cleanly when transformers absent

## Acceptance
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_tools_news.py -v
ruff check src/finroot/tools/news.py src/finroot/tools/sentiment.py
```

## Report
`work/reports/wave-3/02-news-sentiment-tools.report.md`
