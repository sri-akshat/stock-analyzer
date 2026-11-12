import yfinance as yf

def fetch_technical_data(ticker):
  stock = yf.Ticker(ticker)
  data = stock.history(period="1y")
  current_price = data['Close'].iloc[-1]
  fifty_two_week_high = data['Close'].max()
  fifty_two_week_low = data['Close'].min()
  moving_average_50 = data['Close'].rolling(window=50).mean().iloc[-1]
  moving_average_200 = data['Close'].rolling(window=200).mean().iloc[-1]
  volume = data['Volume'].iloc[-1]
  avg_volume = data['Volume'].mean()

  technicals = {
      "current_price": current_price,
      "fifty_two_week_high": fifty_two_week_high,
      "fifty_two_week_low": fifty_two_week_low,
      "moving_average_50": moving_average_50,
      "moving_average_200": moving_average_200,
      "volume": volume,
      "average_volume": avg_volume
  }
  return technicals