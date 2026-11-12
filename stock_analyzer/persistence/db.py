"""SQLite persistence (backlog item 13): signals, consults, decisions and
outcomes, so live performance can later be measured against backtests.
Stdlib sqlite3 only; the database file is created lazily.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ..config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    action TEXT NOT NULL,
    strength REAL,
    reason TEXT,
    backtest_metrics TEXT
);
CREATE TABLE IF NOT EXISTS consults (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    signal_action TEXT,
    verdict TEXT,
    confidence REAL,
    risks TEXT,
    rationale TEXT,
    provider TEXT
);
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    decision TEXT NOT NULL,       -- took | skipped | deferred
    signal_id INTEGER,
    note TEXT
);
CREATE TABLE IF NOT EXISTS outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    signal_id INTEGER,
    pnl_pct REAL,
    detail TEXT
);
CREATE TABLE IF NOT EXISTS paper_positions (
    symbol TEXT PRIMARY KEY,
    quantity INTEGER NOT NULL,
    entry_price REAL NOT NULL,
    entry_ts TEXT NOT NULL,
    stop_price REAL
);
CREATE TABLE IF NOT EXISTS paper_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    pnl REAL
);
"""


class Store:
    def __init__(self, path: str | None = None):
        self.path = Path(path or get_settings().db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def record_signal(self, symbol: str, strategy: str, action: str,
                      strength: float, reason: str,
                      backtest_metrics: dict | None = None) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO signals (ts, symbol, strategy, action, strength, reason, backtest_metrics)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self._now(), symbol, strategy, action, strength, reason,
                 json.dumps(backtest_metrics or {})),
            )
            return int(cur.lastrowid)

    def record_consult(self, verdict) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO consults (ts, symbol, signal_action, verdict, confidence, risks, rationale, provider)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (self._now(), verdict.symbol, verdict.signal_action, verdict.verdict,
                 verdict.confidence, json.dumps(verdict.risks), verdict.rationale,
                 verdict.provider),
            )
            return int(cur.lastrowid)

    def record_decision(self, symbol: str, decision: str, signal_id: int | None = None,
                        note: str = "") -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO decisions (ts, symbol, decision, signal_id, note) VALUES (?, ?, ?, ?, ?)",
                (self._now(), symbol, decision, signal_id, note),
            )
            return int(cur.lastrowid)

    def recent_signals(self, limit: int = 50) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM signals ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    # --- paper trading tables -------------------------------------------

    def open_paper(self, symbol: str, quantity: int, price: float,
                   stop_price: float | None) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO paper_positions (symbol, quantity, entry_price, entry_ts, stop_price)"
                " VALUES (?, ?, ?, ?, ?)",
                (symbol, quantity, price, self._now(), stop_price))
            conn.execute(
                "INSERT INTO paper_trades (ts, symbol, action, quantity, price, pnl)"
                " VALUES (?, ?, 'buy', ?, ?, NULL)",
                (self._now(), symbol, quantity, price))

    def close_paper(self, symbol: str, price: float, pnl: float) -> None:
        with self._conn() as conn:
            pos = conn.execute(
                "SELECT quantity FROM paper_positions WHERE symbol = ?", (symbol,)).fetchone()
            if pos:
                conn.execute(
                    "INSERT INTO paper_trades (ts, symbol, action, quantity, price, pnl)"
                    " VALUES (?, ?, 'sell', ?, ?, ?)",
                    (self._now(), symbol, pos["quantity"], price, pnl))
            conn.execute("DELETE FROM paper_positions WHERE symbol = ?", (symbol,))

    def open_paper_position(self, symbol: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM paper_positions WHERE symbol = ?", (symbol,)).fetchone()
            return dict(row) if row else None

    def open_paper_positions(self) -> list[dict]:
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM paper_positions").fetchall()]

    def paper_trade_count(self) -> int:
        with self._conn() as conn:
            return int(conn.execute(
                "SELECT COUNT(*) AS n FROM paper_trades WHERE action = 'sell'").fetchone()["n"])

    def paper_realized_pnl(self) -> float:
        with self._conn() as conn:
            row = conn.execute("SELECT COALESCE(SUM(pnl), 0) AS pnl FROM paper_trades").fetchone()
            return float(row["pnl"])

    def paper_cash(self, initial_capital: float) -> float:
        with self._conn() as conn:
            bought = conn.execute(
                "SELECT COALESCE(SUM(quantity * price), 0) AS v FROM paper_trades WHERE action = 'buy'"
            ).fetchone()["v"]
            sold = conn.execute(
                "SELECT COALESCE(SUM(quantity * price), 0) AS v FROM paper_trades WHERE action = 'sell'"
            ).fetchone()["v"]
            return float(initial_capital - bought + sold)

    def consult_agreement(self) -> dict:
        """How often the SOTA consult agrees vs disagrees (feeds item 16)."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT verdict, COUNT(*) AS n FROM consults GROUP BY verdict").fetchall()
            return {r["verdict"]: r["n"] for r in rows}
