import yfinance as yf

def analyze_trend(ticker):
  """
  Analyze trend for the given ticker based on technical indicators.

  Parameters:
      ticker (str): Stock ticker symbol (e.g., 'AMD').

  Returns:
      dict: Analysis based on moving averages and support/resistance levels.
  """
  # Fetch historical data for the stock
  stock = yf.Ticker(ticker)
  historical_data = stock.history(period="1y")

  if "Close" not in historical_data.columns:
    print("Unexpected data format. 'Close' column is missing or not in the correct format.")
    return {}

  # Calculate moving averages
  historical_data['MA_50'] = historical_data['Close'].rolling(window=50).mean()
  historical_data['MA_200'] = historical_data['Close'].rolling(window=200).mean()

  # Calculate current price
  current_price = historical_data['Close'].iloc[-1]

  # Identify support and resistance levels
  support_level = historical_data['Close'].min()
  resistance_level = historical_data['Close'].max()

  # Prepare the trend analysis data
  trend_analysis = {
      "current_price": current_price,
      "MA_50": historical_data['MA_50'].iloc[-1],
      "MA_200": historical_data['MA_200'].iloc[-1],
      "support_level": support_level,
      "resistance_level": resistance_level
  }

  print("Trend Analysis:", trend_analysis)
  return trend_analysis

# Detect dynamic support levels based on recent lows
def detect_dynamic_support_levels(stock_data, window=20, threshold=0.01):
  recent_lows = stock_data['Close'].rolling(window=window).min().dropna()
  avg_low = mean(recent_lows[-window:])
  dynamic_support_levels = [level for level in recent_lows if abs(level - avg_low) / avg_low < threshold]
  return list(set(dynamic_support_levels))