import pandas as pd

from stock_analyzer.backtest import BacktestEngine, compute_metrics
from stock_analyzer.risk import RiskConfig, RiskEngine
from stock_analyzer.strategies.base import Strategy
from stock_analyzer.types import Action, Signal


class SpyStrategy(Strategy):
    """Records the latest timestamp visible in each snapshot it receives."""
    name = "spy"
    min_history = 5

    def __init__(self):
        self.seen_until = []

    def generate(self, snapshot):
        assert snapshot.history.index.max() == snapshot.as_of  # the core guarantee
        self.seen_until.append(snapshot.as_of)
        return Signal(Action.HOLD)


class AlwaysBuy(Strategy):
    name = "always_buy"
    min_history = 3

    def generate(self, snapshot):
        if not hasattr(self, "bought"):
            self.bought = True
            return Signal(Action.BUY, 1.0, "test buy")
        return Signal(Action.HOLD)


def test_engine_never_leaks_future(ohlcv):
    df = ohlcv([100 + i * 0.1 for i in range(120)])
    spy = SpyStrategy()
    BacktestEngine().run("TEST", df, spy)
    assert len(spy.seen_until) > 0
    # every snapshot ended at or before the final bar
    assert max(spy.seen_until) == df.index[-1]


def test_buy_executes_at_next_open(ohlcv):
    df = ohlcv([100.0] * 30)
    strat = AlwaysBuy()
    result = BacktestEngine(commission_rate=0.0, slippage_rate=0.0).run("TEST", df, strat)
    buys = [t for t in result.trades if t.action is Action.BUY]
    assert len(buys) == 1
    # signal fires at close of bar i>=3, fills at the NEXT bar's open
    assert buys[0].timestamp == df.index[4]
    assert buys[0].price == float(df["Open"].iloc[4])


def test_stop_loss_exits_position(ohlcv):
    # buy early, then a crash far below the 5% stop
    closes = [100.0] * 10 + [80.0] * 10
    df = ohlcv(closes)
    risk = RiskEngine(RiskConfig(stop_loss_pct=0.05))
    result = BacktestEngine(risk=risk, commission_rate=0.0,
                            slippage_rate=0.0).run("TEST", df, AlwaysBuy())
    sells = [t for t in result.trades if t.action is Action.SELL]
    assert sells, "stop loss should have closed the position"
    assert sells[0].price <= 95.0  # stopped near 95, not ridden down to 80
    assert result.final_position is None


def test_metrics_peak_to_trough_drawdown():
    equity = pd.Series([100, 120, 90, 110, 60, 100],
                       index=pd.date_range("2024-01-01", periods=6, freq="D"))
    m = compute_metrics(equity, [], 100)
    # peak 120 -> trough 60 = -50%, not min/initial (60%)
    assert m["max_drawdown_pct"] == -50.0
    assert m["total_return_pct"] == 0.0


def test_metrics_win_rate():
    equity = pd.Series([100, 105, 110], index=pd.date_range("2024-01-01", periods=3, freq="D"))
    from stock_analyzer.types import Trade
    trades = [
        Trade("T", Action.BUY, 1, 100.0, equity.index[0]),
        Trade("T", Action.SELL, 1, 110.0, equity.index[1]),   # win
        Trade("T", Action.BUY, 1, 110.0, equity.index[1]),
        Trade("T", Action.SELL, 1, 105.0, equity.index[2]),   # loss
    ]
    m = compute_metrics(equity, trades, 100)
    assert m["win_rate_pct"] == 50.0
    assert m["num_trades"] == 4


def test_open_position_counts_in_equity(ohlcv):
    df = ohlcv([100.0] * 29 + [150.0])  # price jumps while holding
    result = BacktestEngine(commission_rate=0.0, slippage_rate=0.0).run(
        "TEST", df, AlwaysBuy())
    assert result.final_position is not None
    # equity must include the marked-to-market gain of the open position
    assert result.equity_curve.iloc[-1] > result.metrics["initial_capital"] * 1.05
