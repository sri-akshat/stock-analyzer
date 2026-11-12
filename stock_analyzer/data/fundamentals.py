"""Fundamental data via yfinance."""
from __future__ import annotations

from .market_data import normalize_symbol, _pace


def get_fundamentals(symbol: str, market: str | None = None) -> dict:
    symbol = normalize_symbol(symbol, market)
    import yfinance as yf

    _pace()
    try:
        info = yf.Ticker(symbol).info or {}
    except Exception:
        return {}
    return {
        "symbol": symbol,
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "price_to_book": info.get("priceToBook"),
        "debt_to_equity": info.get("debtToEquity"),
        "dividend_yield": info.get("dividendYield"),
        "revenue": info.get("totalRevenue"),
        "revenue_growth": info.get("revenueGrowth"),
        "gross_profit": info.get("grossProfits"),
        "beta": info.get("beta"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
    }


def pe_evaluation(pe_ratio: float | None) -> str:
    """The original repo's rule, kept as an explicit, testable function."""
    if pe_ratio is None:
        return "unknown"
    return "undervalued" if pe_ratio < 15 else "overvalued"
