"""Paper trading (backlog item 14): simulate fills on recommendations and
track a virtual portfolio, before any suggestion meets real money.

Positions and fills live in the Store (paper_positions / paper_trades).
"""
from __future__ import annotations

from dataclasses import dataclass

from .persistence import Store
from .recommend import Recommendation
from .risk import RiskEngine
from .types import Action


@dataclass
class PaperAccount:
    cash: float
    realized_pnl: float = 0.0


class PaperTrader:
    def __init__(self, store: Store, risk: RiskEngine | None = None,
                 initial_capital: float = 100_000.0):
        self.store = store
        self.risk = risk or RiskEngine()
        self.initial_capital = initial_capital

    def apply(self, rec: Recommendation, current_price: float) -> dict:
        """Act virtually on one recommendation. Returns a description of
        what the paper account did."""
        if rec.action is Action.BUY:
            return self._buy(rec, current_price)
        if rec.action is Action.SELL:
            return self._sell(rec, current_price)
        return {"symbol": rec.symbol, "did": "nothing"}

    def _buy(self, rec: Recommendation, price: float) -> dict:
        if self.store.open_paper_position(rec.symbol):
            return {"symbol": rec.symbol, "did": "already holding"}
        cash = self.store.paper_cash(self.initial_capital)
        qty = self.risk.position_size(price, self.initial_capital, cash, rec.strength)
        if qty <= 0:
            return {"symbol": rec.symbol, "did": "no size"}
        self.store.open_paper(rec.symbol, qty, price, self.risk.stop_price(price))
        return {"symbol": rec.symbol, "did": "bought", "quantity": qty, "price": price}

    def _sell(self, rec: Recommendation, price: float) -> dict:
        pos = self.store.open_paper_position(rec.symbol)
        if not pos:
            return {"symbol": rec.symbol, "did": "nothing to sell"}
        pnl = (price - pos["entry_price"]) * pos["quantity"]
        self.store.close_paper(rec.symbol, price, pnl)
        return {"symbol": rec.symbol, "did": "sold", "quantity": pos["quantity"],
                "price": price, "pnl": round(pnl, 2)}

    def summary(self) -> dict:
        return {
            "cash": round(self.store.paper_cash(self.initial_capital), 2),
            "open_positions": self.store.open_paper_positions(),
            "closed_trades": self.store.paper_trade_count(),
            "realized_pnl": round(self.store.paper_realized_pnl(), 2),
        }
