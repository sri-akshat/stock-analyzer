class RefreshPolicy:
  """Defines the refresh frequency for each attribute in seconds."""
  def __init__(self, price_refresh=60, volume_refresh=60, news_refresh=300, tech_refresh=3600, fund_refresh=7776000):
    self.price_refresh = price_refresh       # Real-time, e.g., every 60 seconds
    self.volume_refresh = volume_refresh     # Real-time, e.g., every 60 seconds
    self.news_refresh = news_refresh         # e.g., every 5 minutes
    self.tech_refresh = tech_refresh         # e.g., every 1 hour
    self.fund_refresh = fund_refresh         # e.g., every quarter (90 days)
