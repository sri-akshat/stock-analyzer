import pandas as pd
import numpy as np
import yfinance as yf
import datetime

from strategy.signal_generator import generate_trading_signal

INITIAL_CAPITAL = 100000
TRADE_SIZE = 100  # Example trade size
RISK_PER_TRADE = 0.02  # 2% risk per trade
COMMISSION_RATE = 0.001  # 0.1% commission rate

def fetch_historical_data(ticker, period="1y"):
  stock = yf.Ticker(ticker)
  data = stock.history(period=period)
  data.columns = ['Date', 'Adj_Close', 'Close', 'High', 'Low', 'Open', 'Volume']
  data.set_index('Date', inplace=True)
  return data

def detect_dynamic_support_levels(stock_data, window=20, threshold=0.01):
  recent_lows = stock_data['Close'].rolling(window=window).min().dropna()
  # Use iloc for positional indexing to get the last 'window' values
  avg_low = recent_lows.iloc[-window:].mean() if len(recent_lows) >= window else recent_lows.mean()
  dynamic_support_levels = [
      level for level in recent_lows if abs(level - avg_low) / avg_low < threshold
  ]
  return list(set(dynamic_support_levels))

def calculate_metrics(trades):
  total_return = trades['Portfolio Value'].iloc[-1] - INITIAL_CAPITAL
  avg_return_per_trade = trades['Profit/Loss'].mean()
  max_drawdown = trades['Portfolio Value'].min() / INITIAL_CAPITAL * 100  # Drawdown in %
  return {
      "Total Return": round(float(total_return), 2),
      "Average Return per Trade": round(float(avg_return_per_trade), 2),
      "Max Drawdown (%)": max_drawdown
  }

def run_backtest(ticker, period="1y"):
  # Fetch historical data
  historical_data = fetch_historical_data(ticker, period=period)

  # Ensure the index is in datetime format
  historical_data.index = pd.to_datetime(historical_data.index, errors='coerce')

  capital = INITIAL_CAPITAL
  portfolio_value = capital
  trades = []  # Track trades and portfolio value over time

  # Extract support and resistance levels once as single values
  support_level = historical_data['Low'].min()
  resistance_level = historical_data['High'].max()

  for index, row in historical_data.iterrows():
    # Use the current row's 'Close' as the current price
    current_price = row['Close']

    # Prepare trend analysis with scalar values
    trend_analysis = {
        "current_price": current_price,
        "support_level": support_level,
        "resistance_level": resistance_level
    }

    # Generate the trading signal
    signal, strength = generate_trading_signal(trend_analysis, None, None)

    # Convert the date appropriately
    if isinstance(index, (pd.Timestamp, datetime.datetime)):
      date_value = index.date()
    else:
      date_value = pd.to_datetime(index).date()

    if signal == "Buy":
      quantity = min(TRADE_SIZE, int(portfolio_value / (current_price * (1 + COMMISSION_RATE))))
      cost = current_price * quantity * (1 + COMMISSION_RATE)
      if portfolio_value >= cost:
        portfolio_value -= cost
        trades.append({
            "Date": date_value,
            "Signal": "Buy",
            "Price": current_price,
            "Quantity": quantity,
            "Portfolio Value": portfolio_value
        })
      else:
        print("Insufficient funds for Buy.")
    elif signal == "Sell" and quantity > 0:
      revenue = current_price * quantity * (1 - COMMISSION_RATE)
      portfolio_value += revenue
      trades.append({
          "Date": date_value,
          "Signal": "Sell",
          "Price": current_price,
          "Quantity": quantity,
          "Portfolio Value": portfolio_value
      })

  # Convert trades to a DataFrame
  trades_df = pd.DataFrame(trades)

  if trades_df.empty:
    print("No trades were generated. Please check the signal logic and conditions.")
    return None, None

  if not trades_df.empty:
    trades_df['Profit/Loss'] = trades_df['Portfolio Value'].diff().fillna(0)

  # Calculate and format metrics
  metrics = calculate_metrics(trades_df)
  formatted_metrics = {
      "Total Return": f"${metrics['Total Return']:.2f}",
      "Average Return per Trade": f"${metrics['Average Return per Trade']:.2f}",
      "Max Drawdown (%)": f"{metrics['Max Drawdown (%)']:.2f}%"
  }

  print("Backtest Metrics:", formatted_metrics)

  # Format trades_df for readability
  trades_df['Date'] = trades_df['Date'].astype(str)
  trades_df['Price'] = trades_df['Price'].map('${:,.2f}'.format)
  trades_df['Quantity'] = trades_df['Quantity'].map('{:,.0f}'.format)
  trades_df['Portfolio Value'] = trades_df['Portfolio Value'].map('${:,.2f}'.format)
  trades_df['Profit/Loss'] = trades_df['Profit/Loss'].map('${:,.2f}'.format)

  # Print the formatted DataFrame
  print(trades_df.to_string(index=False))

  return trades_df, metrics

# Run the backtest
run_backtest("AMD")