import numpy as np
import pandas as pd

from stock_analyzer import indicators


def test_rsi_bounds_and_flat_series():
    close = pd.Series(np.linspace(100, 120, 60))  # steady uptrend
    value = indicators.rsi(close).iloc[-1]
    assert 0 <= value <= 100
    assert value > 70  # persistent gains should read overbought-ish


def test_rolling_support_is_causal():
    """Support at bar t must equal the trailing-window min ending at t,
    and must never incorporate later bars."""
    close = pd.Series([10, 9, 11, 8, 12, 7, 15, 6, 20, 25], dtype=float)
    sup = indicators.rolling_support(close, window=3)
    for t in range(2, len(close)):  # first window-1 bars are NaN by design
        expected = close.iloc[t - 2: t + 1].min()
        assert sup.iloc[t] == expected
    # truncating the future must not change earlier values
    truncated = indicators.rolling_support(close.iloc[:6], window=3)
    pd.testing.assert_series_equal(sup.iloc[:6], truncated)


def test_dynamic_support_levels_no_missing_import():
    close = pd.Series([100, 99, 101, 99.5, 100.5, 99.2] * 5, dtype=float)
    levels = indicators.dynamic_support_levels(close, window=5, threshold=0.02)
    assert isinstance(levels, list)
    assert all(isinstance(x, float) for x in levels)


def test_macd_columns():
    close = pd.Series(np.sin(np.linspace(0, 6, 100)) * 10 + 100)
    df = indicators.macd(close)
    assert {"macd", "signal", "hist"} <= set(df.columns)
