"""News headlines: yfinance first, Finviz scraping as fallback.

Finviz's CSS class names change without notice, so the scraper is a
best-effort fallback behind the API-shaped yfinance feed.
"""
from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from .market_data import normalize_symbol, _pace


def get_news(symbol: str, limit: int = 10, market: str | None = None) -> list[dict]:
    symbol = normalize_symbol(symbol, market)
    articles = _news_yfinance(symbol, limit)
    if not articles:
        articles = _news_finviz(symbol, limit)
    return articles


def _news_yfinance(symbol: str, limit: int) -> list[dict]:
    import yfinance as yf

    _pace()
    try:
        raw = yf.Ticker(symbol).news or []
    except Exception:
        return []
    out = []
    for item in raw[:limit]:
        content = item.get("content", item)  # yfinance changed shape in 0.2.31+
        title = content.get("title") or item.get("title")
        link = (content.get("canonicalUrl") or {}).get("url") or item.get("link")
        published = content.get("pubDate") or item.get("providerPublishTime")
        if title:
            out.append({"title": title, "url": link, "published_at": published})
    return out


def _news_finviz(symbol: str, limit: int) -> list[dict]:
    _pace()
    try:
        resp = requests.get(
            f"https://finviz.com/quote.ashx?t={symbol}",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=15,
        )
    except Exception:
        return []
    if resp.status_code != 200:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", {"class": "fullview-news-outer"})
    if not table:
        return []
    out = []
    for row in table.find_all("tr")[:limit]:
        cells = row.find_all("td")
        if len(cells) < 2 or not cells[1].a:
            continue
        out.append({
            "title": cells[1].a.text.strip(),
            "url": cells[1].a.get("href"),
            "published_at": cells[0].text.strip(),
        })
    return out
