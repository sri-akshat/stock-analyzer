import yfinance as yf
import pandas as pd

def fetch_historical_data(ticker, period='1y', interval='1d'):
  """
  Fetch historical stock data for the given ticker using yfinance.

  Parameters:
      ticker (str): Stock ticker symbol (e.g., 'AMD').
      period (str): Data period (e.g., '1y' for one year, '6mo' for six months).
      interval (str): Data interval (e.g., '1h' for hourly, '1d' for daily).

  Returns:
      pd.DataFrame: DataFrame containing historical stock data with standardized column names.
  """
  try:
    # Fetch historical data using yfinance
    stock_data = yf.download(ticker, period=period, interval=interval)

    # Print raw data to inspect its structure
    print("Raw data fetched from yfinance:")
    print(stock_data.head())

    # Check if data is fetched and structured correctly
    if stock_data.empty:
      print(f"No data fetched for ticker {ticker}.")
      return pd.DataFrame()  # Return an empty DataFrame if no data is fetched

    # Reset index to make 'Datetime' a column instead of the index and rename columns explicitly if needed
    stock_data.reset_index(inplace=True)

    # Print cleaned data structure
    print("Cleaned data structure:")
    print(stock_data.head())
    return stock_data
  except Exception as e:
    print(f"Error fetching data for {ticker}: {e}")
    return pd.DataFrame()

# Example usage
# historical_data = fetch_historical_data('AMD')
# print("Processed Historical Data:")
# print(historical_data.head())