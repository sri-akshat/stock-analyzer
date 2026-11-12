class TechnicalIndicator:
  def __init__(self,
      moving_average_50=None,
      moving_average_200=None,
      RSI=None,
      MACD=None,
      volatility=None,
      put_call_ratio=None,
      open_interest_call=None,
      open_interest_put=None):
    self.moving_average_50 = moving_average_50      # 50-day moving average
    self.moving_average_200 = moving_average_200    # 200-day moving average
    self.RSI = RSI                                  # Relative Strength Index
    self.MACD = MACD                                # Moving Average Convergence Divergence
    self.volatility = volatility                    # Price volatility
    self.put_call_ratio = put_call_ratio            # Put-to-call ratio
    self.open_interest_call = open_interest_call    # Open interest for call options
    self.open_interest_put = open_interest_put      # Open interest for put options

  def __repr__(self):
    return (f"TechnicalIndicator(moving_average_50={self.moving_average_50}, moving_average_200={self.moving_average_200}, "
            f"RSI={self.RSI}, MACD={self.MACD}, volatility={self.volatility}, put_call_ratio={self.put_call_ratio}, "
            f"open_interest_call={self.open_interest_call}, open_interest_put={self.open_interest_put})")