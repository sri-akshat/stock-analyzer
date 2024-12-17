class PortfolioSetting:
  def __init__(self, risk_tolerance="medium", max_exposure_per_asset=0.1, stop_loss_threshold=0.05):
    self.risk_tolerance = risk_tolerance
    self.max_exposure_per_asset = max_exposure_per_asset
    self.stop_loss_threshold = stop_loss_threshold