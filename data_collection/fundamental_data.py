import yfinance as yf

def fetch_fundamentals(ticker):
  """
  Fetches fundamental data for the specified ticker.

  Args:
      ticker (str): Stock ticker symbol (e.g., 'AMD').

  Returns:
      dict: A dictionary containing fundamental data (e.g., market cap, PE ratio).
  """
  stock = yf.Ticker(ticker)
  info = stock.info
  fundamentals = {
      "market_cap": info.get("marketCap"),
      "pe_ratio": info.get("trailingPE"),
      "dividend_yield": info.get("dividendYield"),
      "revenue": info.get("totalRevenue"),
      "gross_profit": info.get("grossProfits")
  }
  return fundamentals