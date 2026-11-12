from stock_analyzer.paper import PaperTrader
from stock_analyzer.persistence import Store
from stock_analyzer.recommend import Recommendation
from stock_analyzer.types import Action


def rec(symbol, action, strength=1.0):
    return Recommendation(symbol=symbol, strategy="test", action=action,
                          strength=strength, reason="t", backtest={})


def test_paper_buy_then_sell(tmp_path):
    store = Store(str(tmp_path / "p.db"))
    trader = PaperTrader(store, initial_capital=100_000)

    out = trader.apply(rec("FAKE", Action.BUY), current_price=100.0)
    assert out["did"] == "bought"
    pos = store.open_paper_position("FAKE")
    assert pos["quantity"] > 0
    assert pos["stop_price"] == 95.0  # default 5% stop

    # buying again while holding is a no-op
    assert trader.apply(rec("FAKE", Action.BUY), 101.0)["did"] == "already holding"

    out = trader.apply(rec("FAKE", Action.SELL), current_price=110.0)
    assert out["did"] == "sold"
    assert out["pnl"] == 10.0 * out["quantity"]
    assert store.open_paper_position("FAKE") is None

    summary = trader.summary()
    assert summary["realized_pnl"] > 0
    assert summary["closed_trades"] == 1
    assert summary["cash"] > 100_000  # cash back plus profit


def test_sell_without_position_is_noop(tmp_path):
    trader = PaperTrader(Store(str(tmp_path / "p.db")))
    assert trader.apply(rec("FAKE", Action.SELL), current_price=100.0)["did"] == "nothing to sell"
