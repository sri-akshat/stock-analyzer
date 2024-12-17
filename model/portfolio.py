class Portfolio:
  def __init__(self, cash_balance=0.0):
    self.cash_balance = cash_balance
    self.holdings = {}

  def add_stock(self, asset_name, quantity):
    if asset_name in self.holdings:
      self.holdings[asset_name] += quantity
    else:
      self.holdings[asset_name] = quantity