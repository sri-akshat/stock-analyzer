"""Causal technical indicators.

Every function returns a Series/values aligned to the input index and
computed only from current and past rows (rolling/expanding windows), so
they are safe to use point-in-time inside a backtest loop.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(window=window, min_periods=window).mean()


def ema(close: pd.Series, window: int) -> pd.Series:
    return close.ewm(span=window, adjust=False, min_periods=window).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100 - (100 / (1 + rs))
    # no losses at all means pure gains: RSI 100, not NaN
    out = out.mask((avg_loss == 0.0) & (avg_gain > 0.0), 100.0)
    return out.fillna(50.0)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": macd_line - signal_line})


def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()


def rolling_support(close: pd.Series, window: int = 60) -> pd.Series:
    """Support at each bar = min close of the trailing window INCLUDING the
    current bar. Unlike a full-period min, this never sees the future."""
    return close.rolling(window=window, min_periods=min(window, max(5, window // 4))).min()


def rolling_resistance(close: pd.Series, window: int = 60) -> pd.Series:
    return close.rolling(window=window, min_periods=min(window, max(5, window // 4))).max()


def dynamic_support_levels(close: pd.Series, window: int = 20, threshold: float = 0.01) -> list[float]:
    """Recent swing lows clustered near their mean (fixed version of the
    old trend_analysis helper, which called mean() without importing it)."""
    recent_lows = close.rolling(window=window).min().dropna()
    if recent_lows.empty:
        return []
    tail = recent_lows.iloc[-window:] if len(recent_lows) >= window else recent_lows
    avg_low = float(tail.mean())
    return sorted({float(level) for level in tail if abs(level - avg_low) / avg_low < threshold})


def annualized_volatility(close: pd.Series, periods_per_year: int = 252) -> float:
    rets = close.pct_change().dropna()
    if rets.empty:
        return 0.0
    return float(rets.std() * np.sqrt(periods_per_year))
