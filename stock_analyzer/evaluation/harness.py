"""Model evaluation harness (backlog item 16).

Joins recorded signals with their realized outcomes and splits performance
by what the SOTA consult said, so over time you can measure whether the
consult calls earn their keep: does following 'agree' signals beat the raw
strategy, and how bad are the 'disagree' signals you would have skipped?
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from ..persistence import Store


def record_outcome(store: Store, symbol: str, signal_id: int,
                   pnl_pct: float, detail: str = "") -> int:
    with store._conn() as conn:
        cur = conn.execute(
            "INSERT INTO outcomes (ts, symbol, signal_id, pnl_pct, detail)"
            " VALUES (?, ?, ?, ?, ?)",
            (datetime.now(timezone.utc).isoformat(), symbol, signal_id, pnl_pct, detail),
        )
        return int(cur.lastrowid)


def performance_report(store: Store) -> dict:
    """Average realized P&L per strategy, and per consult verdict."""
    with store._conn() as conn:
        by_strategy = conn.execute(
            """SELECT s.strategy, COUNT(o.id) AS n, AVG(o.pnl_pct) AS avg_pnl
               FROM outcomes o JOIN signals s ON s.id = o.signal_id
               GROUP BY s.strategy""").fetchall()
        by_verdict = conn.execute(
            """SELECT COALESCE(c.verdict, 'no_consult') AS verdict,
                      COUNT(o.id) AS n, AVG(o.pnl_pct) AS avg_pnl
               FROM outcomes o
               JOIN signals s ON s.id = o.signal_id
               LEFT JOIN consults c ON c.symbol = s.symbol
               GROUP BY verdict""").fetchall()
    return {
        "by_strategy": {r["strategy"]: {"n": r["n"], "avg_pnl_pct": _r(r["avg_pnl"])}
                        for r in by_strategy},
        "by_consult_verdict": {r["verdict"]: {"n": r["n"], "avg_pnl_pct": _r(r["avg_pnl"])}
                               for r in by_verdict},
    }


def _r(x) -> float | None:
    return round(float(x), 3) if x is not None else None
