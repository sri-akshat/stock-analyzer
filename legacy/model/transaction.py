class Transaction:
  def __init__(self, asset_name, transaction_type, quantity, price, timestamp):
    self.asset_name = asset_name
    self.transaction_type = transaction_type
    self.quantity = quantity
    self.price = price
    self.timestamp = timestamp