from data_collection import fetch_fundamentals


def analyze_fundamentals(ticker):
  """
  Analyze fundamental data for the given ticker.

  Parameters:
      ticker (str): Stock ticker symbol (e.g., 'AMD').

  Returns:
      dict: Analysis based on fundamental data.
  """
  # Fetch fundamental data
  fundamentals = fetch_fundamentals(ticker)
  print("Fetched Fundamentals:", fundamentals)  # Debugging line to check data structure

  # Ensure fundamentals is a dictionary
  if not isinstance(fundamentals, dict):
    print("Unexpected data type for fundamentals:", type(fundamentals))
    return {}  # Return an empty dictionary or handle this case as needed

  # Retrieve fundamental metrics
  pe_ratio = fundamentals.get("pe_ratio", 0)
  market_cap = fundamentals.get("market_cap", 0)
  dividend_yield = fundamentals.get("dividend_yield", None)
  revenue = fundamentals.get("revenue", 0)
  gross_profit = fundamentals.get("gross_profit", 0)

  # Evaluate P/E ratio
  pe_evaluation = "Undervalued" if pe_ratio < 15 else "Overvalued"

  fundamental_analysis = {
      "pe_evaluation": pe_evaluation,
      "market_cap": market_cap,
      "dividend_yield": dividend_yield,
      "revenue": revenue,
      "gross_profit": gross_profit,
  }

  print("Fundamental Analysis:", fundamental_analysis)
  return fundamental_analysis