"""Scheduled runs (backlog item 12).

`daily_scan` is the unit of work: scan the universe, persist signals, apply
them to the paper portfolio, and return an alert-ready summary. Schedule it
from cron or GitHub Actions - no long-running daemon needed:

  # crontab: weekdays after US market close, 8:05 AM IST
  5 8 * * 1-5  cd /path/to/repo && python -m stock_analyzer.jobs AMD MSFT NVDA

Alerts: the summary dict is returned and printed; wire `alert_sink` to
email/WhatsApp/webhook when a delivery channel is chosen.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from .data import get_ohlcv
from .paper import PaperTrader
from .persistence import Store
from .recommend import RecommendationEngine


def daily_scan(universe: list[str], market: str | None = None,
               strategy: str = "composite", alert_sink=None) -> dict:
    store = Store()
    engine = RecommendationEngine(store=store)
    paper = PaperTrader(store)

    recs = engine.scan(universe, market=market)
    fills = []
    for rec in recs:
        history = get_ohlcv(rec.symbol, period="5d", market=market)
        if history.empty:
            continue
        fills.append(paper.apply(rec, float(history["Close"].iloc[-1])))

    summary = {
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "universe": universe,
        "recommendations": [
            {"symbol": r.symbol, "action": r.action.value, "strength": r.strength,
             "reason": r.reason, "score": r.score,
             "backtest": r.backtest, "consult": r.consult}
            for r in recs
        ],
        "paper_fills": fills,
        "paper_portfolio": paper.summary(),
    }
    if alert_sink:
        alert_sink(summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stock-analyzer-jobs")
    parser.add_argument("symbols", nargs="+")
    parser.add_argument("--market", default=None)
    args = parser.parse_args(argv)
    summary = daily_scan(args.symbols, market=args.market)
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
