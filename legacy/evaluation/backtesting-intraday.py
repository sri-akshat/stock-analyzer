import pandas as pd
import datetime
import yfinance as yf

# Constants
INITIAL_CAPITAL = 100000  # Starting capital
TRADE_SIZE = 100  # Number of shares to trade
COMMISSION_RATE = 0.01  # 1% commission

def fetch_intraday_data(ticker, interval="5m", period="5d"):
  # Fetch intraday historical data (e.g., 5-minute intervals for 1 day)
  stock = yf.Ticker(ticker)
  return stock.history(interval=interval, period=period)

def generate_trading_signal(trend_analysis):
  # Example logic for generating Buy, Sell, or Hold signals based on support and resistance levels
  current_price = trend_analysis["current_price"]
  support_level = trend_analysis["support_level"]
  resistance_level = trend_analysis["resistance_level"]

  if current_price < support_level * 0.98:  # Buying condition, e.g., if price is near/below support
    return "Buy", "Strong"
  elif current_price > resistance_level * 1.02:  # Selling condition, e.g., if price is near/above resistance
    return "Sell", "Strong"
  else:
    return "Hold", "Neutral"  # Hold signal for non-ideal conditions

def calculate_metrics(trades):
  total_return = trades['Portfolio Value'].iloc[-1] - INITIAL_CAPITAL
  avg_return_per_trade = trades['Profit/Loss'].mean()
  max_drawdown = trades['Portfolio Value'].min() / INITIAL_CAPITAL * 100  # Drawdown in %
  return {
      "Total Return": round(float(total_return), 2),
      "Average Return per Trade": round(float(avg_return_per_trade), 2),
      "Max Drawdown (%)": max_drawdown
  }

def run_backtest(ticker, interval="1h", period="3mo", start_date=None, end_date=None):
  # Fetch historical intraday data
  historical_data = fetch_intraday_data(ticker, interval=interval, period=period)

  # Filter for specific date range if provided
  if start_date and end_date:
    historical_data = historical_data[(historical_data.index >= start_date) &
                                      (historical_data.index <= end_date)]

  capital = INITIAL_CAPITAL
  portfolio_value = capital
  holdings = 0
  trades = []

  # Ensure support and resistance levels are defined for conditions
  SUPPORT_LEVEL = 100  # example support level
  RESISTANCE_LEVEL = 200  # example resistance level

  for index, row in historical_data.iterrows():
    current_price = row['Close']

    if current_price < SUPPORT_LEVEL and portfolio_value >= current_price:
      quantity = int(portfolio_value // current_price)
      cost = quantity * current_price
      portfolio_value -= cost
      holdings += quantity
      trades.append({
          "Date": index,
          "Signal": "Buy",
          "Price": current_price,
          "Quantity": quantity,
          "Portfolio Value": portfolio_value
      })

    elif current_price > RESISTANCE_LEVEL and holdings > 0:
      revenue = holdings * current_price
      portfolio_value += revenue
      trades.append({
          "Date": index,
          "Signal": "Sell",
          "Price": current_price,
          "Quantity": holdings,
          "Portfolio Value": portfolio_value
      })
      holdings = 0

  # Check if trades were executed
  if not trades:
    print("No trades were executed. Check the buy/sell conditions or ensure data availability.")
    return pd.DataFrame(), {}

  # Convert trades to DataFrame
  trades_df = pd.DataFrame(trades)

  # Calculate Profit/Loss based on Portfolio Value changes
  trades_df['Profit/Loss'] = trades_df['Portfolio Value'].diff().fillna(0)

  # Calculate and print performance metrics
  metrics = calculate_metrics(trades_df)
  print("Backtest Metrics:", metrics)
  print(trades_df.to_string(index=False))

  return trades_df, metrics

# Run backtest for the given date range
run_backtest("AMD", interval="1h", period="3mo", start_date="2024-10-05", end_date="2024-12-06")