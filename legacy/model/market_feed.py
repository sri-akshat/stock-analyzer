from datetime import datetime

from model.fundamental_indicator import FundamentalIndicator
from model.refresh_policy import RefreshPolicy
from model.technical_indicator import TechnicalIndicator


class MarketFeed:
  _instances = {}  # Dictionary to store instances by stock symbol

  def __new__(cls, asset_name, *args, **kwargs):
    if asset_name not in cls._instances:
      instance = super(MarketFeed, cls).__new__(cls)
      cls._instances[asset_name] = instance
    return cls._instances[asset_name]

  def __init__(self, asset_name, price, volume, price_history=None, news=None, technical_data=None, fundamental_data=None, refresh_policy=None):
    if not hasattr(self, 'initialized'):  # Prevent reinitialization
      self.asset_name = asset_name
      self.current_price = price
      self.volume = volume
      self.price_history = price_history if price_history else []
      self.news = news if news else []
      self.technical_data = technical_data if technical_data else TechnicalIndicator()
      self.fundamental_data = fundamental_data if fundamental_data else FundamentalIndicator()
      self.refresh_policy = refresh_policy if refresh_policy else RefreshPolicy()
      self.last_refresh_times = {
          "price": datetime.now(),
          "volume": datetime.now(),
          "news": datetime.now(),
          "technical": datetime.now(),
          "fundamental": datetime.now()
      }
      self.initialized = True  # Mark as initialized to prevent reinitialization

  def should_refresh(self, attribute):
    """Determines if the attribute needs refreshing based on last refresh time and policy."""
    now = datetime.now()
    time_elapsed = (now - self.last_refresh_times[attribute]).total_seconds()

    # Check if time since last refresh exceeds policy for the given attribute
    if attribute == "price" and time_elapsed >= self.refresh_policy.price_refresh:
      return True
    elif attribute == "volume" and time_elapsed >= self.refresh_policy.volume_refresh:
      return True
    elif attribute == "news" and time_elapsed >= self.refresh_policy.news_refresh:
      return True
    elif attribute == "technical" and time_elapsed >= self.refresh_policy.tech_refresh:
      return True
    elif attribute == "fundamental" and time_elapsed >= self.refresh_policy.fund_refresh:
      return True
    return False

  @classmethod
  def get_instance(cls, asset_name):
    """Retrieve an existing instance for a stock or create one if it doesn't exist."""
    return cls._instances.get(asset_name)

# Usage example:
# Creating or retrieving MarketFeed for "AAPL"
apple_feed = MarketFeed("AAPL", 150.0, 100000)
another_apple_feed = MarketFeed("AAPL", 151.0, 101000)  # Returns the same instance as above
google_feed = MarketFeed("GOOGL", 2800.0, 50000)  # Separate instance for Google stock

# Check if instances are unique per stock
print(apple_feed is another_apple_feed)  # True
print(apple_feed is google_feed)  # False