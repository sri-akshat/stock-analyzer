import numpy as np
import pandas as pd
import pytest


def make_ohlcv(closes, start="2024-01-01"):
    """Build an OHLCV frame from a list of close prices."""
    closes = np.asarray(closes, dtype=float)
    idx = pd.date_range(start=start, periods=len(closes), freq="B")
    return pd.DataFrame({
        "Open": closes * 0.999,
        "High": closes * 1.01,
        "Low": closes * 0.99,
        "Close": closes,
        "Volume": 1_000_000,
    }, index=idx)


@pytest.fixture
def ohlcv():
    return make_ohlcv
