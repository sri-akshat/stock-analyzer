"""Streamlit dashboard (backlog item 15).

  streamlit run dashboard/app.py

Pages: Today's suggestions | Signal history | Paper portfolio | Backtest explorer
Reads the same SQLite store the CLI writes; nothing here places real trades.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stock_analyzer.config import get_settings  # noqa: E402

st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("Stock Analyzer")
st.caption("Backtested strategy suggestions - recommendations only, no auto-trading.")

db_path = get_settings().db_path


def q(sql: str, params=()) -> pd.DataFrame:
    if not Path(db_path).exists():
        return pd.DataFrame()
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


tab_today, tab_signals, tab_paper, tab_backtest = st.tabs(
    ["Signals", "History", "Paper portfolio", "Backtest explorer"])

with tab_today:
    st.subheader("Latest signals per symbol")
    df = q("""
        SELECT s.ts, s.symbol, s.strategy, s.action, s.strength, s.reason
        FROM signals s
        WHERE s.id IN (SELECT MAX(id) FROM signals GROUP BY symbol, strategy)
        ORDER BY s.ts DESC
    """)
    st.dataframe(df, use_container_width=True) if not df.empty else st.info(
        "No signals yet. Run: python -m stock_analyzer.cli recommend AMD MSFT")

    st.subheader("SOTA consult agreement")
    agrees = q("SELECT verdict, COUNT(*) AS n FROM consults GROUP BY verdict")
    if agrees.empty:
        st.info("No consults recorded yet (the layer is off until an LLM key is set).")
    else:
        st.bar_chart(agrees.set_index("verdict"))

with tab_signals:
    st.subheader("All recorded signals")
    df = q("SELECT ts, symbol, strategy, action, strength, reason FROM signals ORDER BY id DESC LIMIT 200")
    st.dataframe(df, use_container_width=True) if not df.empty else st.info("Empty.")

with tab_paper:
    st.subheader("Open paper positions")
    pos = q("SELECT * FROM paper_positions")
    st.dataframe(pos, use_container_width=True) if not pos.empty else st.info("No open paper positions.")
    st.subheader("Paper fills")
    trades = q("SELECT ts, symbol, action, quantity, price, pnl FROM paper_trades ORDER BY id DESC LIMIT 200")
    st.dataframe(trades, use_container_width=True) if not trades.empty else st.info("No paper fills yet.")
    pnl = q("SELECT COALESCE(SUM(pnl), 0) AS realized FROM paper_trades")
    st.metric("Realized paper P&L", f"${float(pnl['realized'].iloc[0]):,.2f}" if not pnl.empty else "$0")

with tab_backtest:
    st.subheader("Run a point-in-time backtest")
    col1, col2, col3 = st.columns(3)
    symbol = col1.text_input("Symbol", "AMD")
    strategy = col2.selectbox("Strategy", ["composite", "support_resistance", "momentum", "mean_reversion"])
    period = col3.selectbox("Period", ["1y", "2y", "4y", "max"], index=1)
    if st.button("Run backtest"):
        from stock_analyzer.backtest import BacktestEngine
        from stock_analyzer.data import get_ohlcv
        from stock_analyzer.strategies import STRATEGIES

        with st.spinner("Fetching data and running..."):
            history = get_ohlcv(symbol, period=period)
            if history.empty:
                st.error(f"No data for {symbol}")
            else:
                result = BacktestEngine().run(symbol, history, STRATEGIES[strategy]())
                m = result.metrics
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Return", f"{m['total_return_pct']}%")
                c2.metric("Sharpe", m["sharpe"])
                c3.metric("Max drawdown", f"{m['max_drawdown_pct']}%")
                c4.metric("Trades", m["num_trades"])
                st.line_chart(result.equity_curve)
                if result.trades:
                    st.dataframe(pd.DataFrame([{
                        "date": t.timestamp.date(), "action": t.action.value,
                        "qty": t.quantity, "price": round(t.price, 2), "reason": t.reason,
                    } for t in result.trades]), use_container_width=True)
