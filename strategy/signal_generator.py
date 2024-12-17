import numpy as np
import pandas as pd


def generate_trading_signal(trend, sentiment, fundamentals):
  # Extract values from Series if they are still Series
  current_price = trend["current_price"].iloc[0] if isinstance(trend["current_price"], pd.Series) else trend["current_price"]
  support_level = trend["support_level"].iloc[0] if isinstance(trend["support_level"], pd.Series) else trend["support_level"]
  resistance_level = trend["resistance_level"].iloc[0] if isinstance(trend["resistance_level"], pd.Series) else trend["resistance_level"]

  # Debugging: print the key values being evaluated
  # print(f"Current Price: {current_price}")
  # print(f"Support Level: {support_level}")
  # print(f"Resistance Level: {resistance_level}")

  # Example trade signal generation
  if current_price <= support_level * 1.01:  # Adjust tolerance if needed
    # print("Buy signal generated.")
    return "Buy", 1
  elif current_price >= resistance_level * 0.99:
    # print("Sell signal generated.")
    return "Sell", 1
  else:
    # print("Hold signal generated.")
    return "Hold", 0

# def generate_trading_signal(trend, sentiment, fundamentals):
#   signal_strength = 0  # This will help determine Buy, Sell, or Hold
#
#   # Technical Signal
#   if trend["current_price"] <= trend["support_level"] * 1.01:  # Near support level
#     if trend["MA_50"] > trend["MA_200"]:  # Uptrend
#       signal_strength += 1  # Strengthen buy signal
#       technical_signal = "buy"
#     else:
#       technical_signal = "hold"  # No strong signal without an uptrend
#   elif trend["current_price"] >= trend["resistance_level"] * 0.99:  # Near resistance level
#     technical_signal = "sell"
#   else:
#     technical_signal = "hold"
#
#   # Sentiment Signal
#   if sentiment["average_polarity"] > 0.2:  # Positive sentiment
#     sentiment_signal = "buy"
#     signal_strength += 0.5  # Boost signal strength slightly
#   elif sentiment["average_polarity"] < -0.2:  # Negative sentiment
#     sentiment_signal = "sell"
#     signal_strength -= 0.5  # Weaken signal strength slightly
#   else:
#     sentiment_signal = "hold"
#
#   # Fundamental Signal
#   if fundamentals["pe_evaluation"] == "Undervalued" and fundamentals["revenue"] > 1e10:  # Strong fundamentals
#     fundamental_signal = "buy"
#     signal_strength += 0.5
#   elif fundamentals["pe_evaluation"] == "Overvalued":
#     fundamental_signal = "sell"
#     signal_strength -= 0.5
#   else:
#     fundamental_signal = "hold"
#
#   # Combine Signals with Weights
#   signals = [technical_signal, sentiment_signal, fundamental_signal]
#   final_signal = "hold"  # Default action
#
#   if signals.count("buy") > 1 and signal_strength > 0.5:
#     final_signal = "buy"
#   elif signals.count("sell") > 1 and signal_strength < -0.5:
#     final_signal = "sell"
#
#   return final_signal, signal_strength