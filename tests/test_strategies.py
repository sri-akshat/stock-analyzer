import pandas as pd

from stock_analyzer.strategies import (CompositeStrategy, MeanReversionStrategy,
                                       MomentumStrategy, SupportResistanceStrategy)
from stock_analyzer.types import Action, MarketSnapshot


def snap(ohlcv_df, symbol="TEST"):
    return MarketSnapshot(symbol=symbol, as_of=ohlcv_df.index[-1], history=ohlcv_df)


def test_support_resistance_buys_near_support(ohlcv):
    # long flat range, then dip to the bottom of it
    closes = [100 + (i % 10) for i in range(80)] + [100.5, 100.2]
    df = ohlcv(closes)
    strat = SupportResistanceStrategy(window=60, tolerance=0.02)
    signal = strat.generate(snap(df))
    assert signal.action is Action.BUY
    assert 0 < signal.strength <= 1


def test_support_resistance_holds_mid_range(ohlcv):
    closes = [100 + (i % 10) for i in range(80)] + [105.0]
    strat = SupportResistanceStrategy(window=60, tolerance=0.01)
    signal = strat.generate(snap(ohlcv(closes)))
    assert signal.action is Action.HOLD


def test_mean_reversion_buys_oversold(ohlcv):
    closes = [100.0] * 30 + [100 - i * 2 for i in range(1, 20)]  # sharp drop
    strat = MeanReversionStrategy(window=14)
    signal = strat.generate(snap(ohlcv(closes)))
    assert signal.action is Action.BUY


def test_momentum_needs_history(ohlcv):
    strat = MomentumStrategy(fast=5, slow=20)
    signal = strat.generate(snap(ohlcv([100.0] * 10)))
    assert signal.action is Action.HOLD  # insufficient history, not a crash


def test_composite_combines_votes(ohlcv):
    closes = [100 + (i % 10) for i in range(80)] + [100.5, 100.2]
    df = ohlcv(closes)
    snapshot = snap(df)
    snapshot.sentiment = {"polarity": 0.6}
    snapshot.fundamentals = {"pe_ratio": 10}
    strat = CompositeStrategy()
    signal = strat.generate(snapshot)
    assert signal.action in (Action.BUY, Action.HOLD)
    assert "composite" in signal.reason
