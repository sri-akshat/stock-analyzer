from stock_analyzer.risk import RiskConfig, RiskEngine
from stock_analyzer.types import Position
import pandas as pd


def test_position_size_respects_exposure_cap():
    engine = RiskEngine(RiskConfig(max_exposure_per_asset=0.10, risk_per_trade=0.50,
                                   stop_loss_pct=0.50))
    # huge risk budget and stop distance: exposure cap must bind
    qty = engine.position_size(price=100, portfolio_value=100_000, cash=100_000)
    assert qty * 100 <= 10_000  # 10% of portfolio


def test_position_size_respects_cash():
    engine = RiskEngine(RiskConfig())
    qty = engine.position_size(price=100, portfolio_value=100_000, cash=500)
    assert qty * 100 <= 500


def test_position_size_respects_risk_budget():
    engine = RiskEngine(RiskConfig(risk_per_trade=0.02, stop_loss_pct=0.05,
                                   max_exposure_per_asset=1.0))
    # risk $2000 on a $5 stop distance -> 400 shares max
    qty = engine.position_size(price=100, portfolio_value=100_000, cash=1_000_000,
                               strength=1.0)
    assert qty <= 400


def test_check_stop():
    engine = RiskEngine(RiskConfig(stop_loss_pct=0.05))
    pos = Position("T", 10, 100.0, pd.Timestamp("2024-01-01"),
                   stop_price=engine.stop_price(100.0))
    assert engine.check_stop(pos, low=94.0)
    assert not engine.check_stop(pos, low=96.0)
