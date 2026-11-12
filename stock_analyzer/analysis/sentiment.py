"""Headline sentiment.

Baseline: TextBlob polarity over recent headlines (the original repo's
approach, now isolated and optional). The function signature accepts any
analyzer callable, so an LLM/finBERT scorer can replace it without touching
callers (backlog item 9).
"""
from __future__ import annotations

from ..data import get_news


def _textblob_score(titles: list[str]) -> dict:
    from textblob import TextBlob

    polarities = [TextBlob(t).sentiment.polarity for t in titles]
    subjectivities = [TextBlob(t).sentiment.subjectivity for t in titles]
    if not polarities:
        return {"polarity": 0.0, "subjectivity": 0.0, "n_headlines": 0}
    return {
        "polarity": sum(polarities) / len(polarities),
        "subjectivity": sum(subjectivities) / len(subjectivities),
        "n_headlines": len(polarities),
    }


def analyze_sentiment(symbol: str, limit: int = 10, market: str | None = None,
                      analyzer=None) -> dict:
    articles = get_news(symbol, limit=limit, market=market)
    titles = [a["title"] for a in articles if a.get("title")]
    scorer = analyzer or _textblob_score
    try:
        scores = scorer(titles)
    except ImportError:
        # textblob not installed: stay neutral rather than crash
        scores = {"polarity": 0.0, "subjectivity": 0.0, "n_headlines": len(titles)}
    scores["headlines"] = titles[:5]
    return scores
