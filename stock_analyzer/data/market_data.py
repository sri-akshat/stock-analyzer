"""Market data via yfinance, with on-disk caching and gentle pacing.

Supports US tickers (AAPL) and NSE tickers (RELIANCE.NS) - pass `market='NS'`
or include the suffix yourself.
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

import pandas as pd

from ..config import get_settings

_LAST_REQUEST = 0.0


def normalize_symbol(symbol: str, market: str | None = None) -> str:
    symbol = symbol.strip().upper()
    if market and market.upper() in {"NS", "NSE"} and not symbol.endswith(".NS"):
        symbol += ".NS"
    return symbol


def _pace() -> None:
    global _LAST_REQUEST
    pause = get_settings().request_pause_seconds
    wait = pause - (time.monotonic() - _LAST_REQUEST)
    if wait > 0:
        time.sleep(wait)
    _LAST_REQUEST = time.monotonic()


def _cache_path(symbol: str, period: str, interval: str) -> Path:
    key = hashlib.sha1(f"{symbol}|{period}|{interval}".encode()).hexdigest()[:16]
    d = Path(get_settings().cache_dir) / "ohlcv"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{key}.pkl"


def get_ohlcv(symbol: str, period: str = "1y", interval: str = "1d",
              market: str | None = None, use_cache: bool = True) -> pd.DataFrame:
    """Return an OHLCV DataFrame indexed by timestamp, columns
    Open/High/Low/Close/Volume. Empty DataFrame on failure (never raises)."""
    symbol = normalize_symbol(symbol, market)
    cache = _cache_path(symbol, period, interval)
    ttl = get_settings().cache_ttl_minutes * 60

    if use_cache and cache.exists() and (time.time() - cache.stat().st_mtime) < ttl:
        return pd.read_pickle(cache)

    import yfinance as yf  # deferred so tests do not need network

    _pace()
    try:
        df = yf.download(symbol, period=period, interval=interval,
                         auto_adjust=True, progress=False)
    except Exception:
        return pd.DataFrame()
    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):  # yfinance returns MultiIndex at times
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df.index = pd.to_datetime(df.index)

    try:
        df.to_pickle(cache)
    except Exception:
        pass  # caching is best-effort
    return df
