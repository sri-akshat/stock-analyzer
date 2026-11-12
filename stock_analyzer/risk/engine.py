"""Risk engine (backlog item 7): position sizing, stop losses, exposure caps.

Turns the old unused PortfolioSetting fields and the dangling 2%
risk-per-trade constant into the rules that actually size and cap trades.
Loss mitigation is half the product objective, so every entry and exit
flows through here.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..config import get_settings
from ..types import Position

# risk tolerance scales how much of the theoretical size we actually take
_TOLERANCE_SCALE = {"low": 0.5, "medium": 1.0, "high": 1.5}


@dataclass(frozen=True)
class RiskConfig:
    risk_tolerance: str = get_settings().risk_tolerance
    max_exposure_per_asset: float = get_settings().max_exposure_per_asset
    stop_loss_pct: float = get_settings().stop_loss_pct
    risk_per_trade: float = get_settings().risk_per_trade


class RiskEngine:
    def __init__(self, config: RiskConfig | None = None):
        self.config = config or RiskConfig()

    def position_size(self, price: float, portfolio_value: float, cash: float,
                      strength: float = 1.0) -> int:
        """Shares to buy: the smallest of
        - risk budget (risk_per_trade of portfolio, given the stop distance)
        - exposure cap (max_exposure_per_asset of portfolio)
        - what cash affords
        scaled by signal strength and risk tolerance.
        """
        if price <= 0 or portfolio_value <= 0:
            return 0
        scale = _TOLERANCE_SCALE.get(self.config.risk_tolerance, 1.0) * max(strength, 0.1)

        stop_distance = max(price * self.config.stop_loss_pct, 1e-9)
        risk_shares = (portfolio_value * self.config.risk_per_trade) / stop_distance
        exposure_shares = (portfolio_value * self.config.max_exposure_per_asset) / price
        cash_shares = cash / price

        shares = int(min(risk_shares, exposure_shares, cash_shares) * scale)
        return max(shares, 0)

    def stop_price(self, entry_price: float) -> float:
        return round(entry_price * (1 - self.config.stop_loss_pct), 4)

    def check_stop(self, position: Position, low: float) -> bool:
        """True if the bar's low breached the position's stop."""
        return position.stop_price is not None and low <= position.stop_price
