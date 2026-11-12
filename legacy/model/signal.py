class Signal:
  def __init__(self, asset_name, signal_type, quantity, timestamp, strength="normal"):
    self.asset_name = asset_name
    self.signal_type = signal_type
    self.quantity = quantity
    self.timestamp = timestamp
    self.strength = strength