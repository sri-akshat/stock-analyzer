"""Recommendation engine: scan a universe, backtest each strategy per
symbol, and rank today's actionable suggestions.

A suggestion is only as good as its evidence, so every recommendation
carries the backtest metrics behind it, the signal reason, and (when
enabled) the SOTA consult verdict. Suggestions are recorded to the Store.
Nothing here places trades - output is advice to the user, full stop.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..backtest import BacktestEngine
from ..consult import ConsultService
from ..data import get_fundamentals, get_ohlcv
from ..persistence import Store
from ..strategies import STRATEGIES
from ..strategies.base import Strategy
from ..types import Action, MarketSnapshot


@dataclass
class Recommendation:
    symbol: str
    strategy: str
    action: Action
    strength: float
    reason: str
    backtest: dict = field(default_factory=dict)
    consult: dict | None = None
    score: float = 0.0  # ranking score: signal strength weighted by evidence


class RecommendationEngine:
    def __init__(self, strategies: list[Strategy] | None = None,
                 backtest_engine: BacktestEngine | None = None,
                 consult: ConsultService | None = None,
                 store: Store | None = None,
                 period: str = "2y"):
        self.strategies = strategies or [STRATEGIES["composite"]()]
        self.backtest_engine = backtest_engine or BacktestEngine()
        self.consult = consult or ConsultService()
        self.store = store
        self.period = period

    def _context_for_consult(self, symbol: str, snapshot: MarketSnapshot,
                             backtest_metrics: dict) -> dict:
        close = snapshot.history["Close"]
        return {
            "price": snapshot.price,
            "pct_change_20d": round(float(close.iloc[-1] / close.iloc[-21] - 1) * 100, 2)
                              if len(close) > 21 else None,
            "pct_change_1y": round(float(close.iloc[-1] / close.iloc[0] - 1) * 100, 2),
            "sentiment": snapshot.sentiment,
            "fundamentals": snapshot.fundamentals,
            "backtest_metrics": backtest_metrics,
        }

    def analyze_symbol(self, symbol: str, market: str | None = None) -> list[Recommendation]:
        history = get_ohlcv(symbol, period=self.period, market=market)
        if history.empty:
            return []
        fundamentals = get_fundamentals(symbol, market=market)

        out: list[Recommendation] = []
        for strategy in self.strategies:
            result = self.backtest_engine.run(symbol, history, strategy,
                                              fundamentals=fundamentals)
            snapshot = MarketSnapshot(symbol=symbol, as_of=history.index[-1],
                                      history=history, fundamentals=fundamentals)
            signal = strategy.generate(snapshot)
            if signal.action is Action.HOLD:
                continue

            sharpe = result.metrics.get("sharpe", 0.0) or 0.0
            score = round(signal.strength * max(sharpe, 0.0), 3)
            rec = Recommendation(symbol=symbol, strategy=strategy.name,
                                 action=signal.action, strength=signal.strength,
                                 reason=signal.reason, backtest=result.metrics,
                                 score=score)

            if self.consult.enabled:
                verdict = self.consult.review(
                    symbol, signal, self._context_for_consult(symbol, snapshot, result.metrics))
                if verdict:
                    rec.consult = {
                        "verdict": verdict.verdict,
                        "confidence": verdict.confidence,
                        "risks": verdict.risks,
                        "rationale": verdict.rationale,
                    }
                    if verdict.verdict == "disagree":
                        rec.score = round(rec.score * (1 - verdict.confidence), 3)

            if self.store:
                signal_id = self.store.record_signal(
                    symbol, strategy.name, signal.action.value,
                    signal.strength, signal.reason, result.metrics)
                if rec.consult and self.consult.enabled:
                    from ..consult.advisor import ConsultVerdict
                    self.store.record_consult(ConsultVerdict(
                        symbol=symbol, signal_action=signal.action.value,
                        verdict=rec.consult["verdict"], confidence=rec.consult["confidence"],
                        risks=rec.consult["risks"], rationale=rec.consult["rationale"],
                        provider=self.consult.provider.name if self.consult.provider else ""))
            out.append(rec)
        return out

    def scan(self, universe: list[str], market: str | None = None) -> list[Recommendation]:
        recs: list[Recommendation] = []
        for symbol in universe:
            recs.extend(self.analyze_symbol(symbol, market=market))
        return sorted(recs, key=lambda r: r.score, reverse=True)
