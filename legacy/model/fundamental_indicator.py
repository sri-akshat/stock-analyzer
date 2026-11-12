class FundamentalIndicator:
  def __init__(self,
      PE_ratio=None,
      EPS=None,
      revenue_growth=None,
      dividend_yield=None,
      market_cap=None,
      institutional_ownership=None,
      beta=None,
      debt_to_equity=None,
      price_to_book=None):
    self.PE_ratio = PE_ratio                        # Price-to-Earnings ratio
    self.EPS = EPS                                  # Earnings per share
    self.revenue_growth = revenue_growth            # Revenue growth rate
    self.dividend_yield = dividend_yield            # Dividend yield
    self.market_cap = market_cap                    # Market capitalization
    self.institutional_ownership = institutional_ownership  # Institutional ownership percentage
    self.beta = beta                                # Stock beta
    self.debt_to_equity = debt_to_equity            # Debt-to-equity ratio
    self.price_to_book = price_to_book              # Price-to-book ratio

  def __repr__(self):
    return (f"FundamentalIndicator(PE_ratio={self.PE_ratio}, EPS={self.EPS}, revenue_growth={self.revenue_growth}, "
            f"dividend_yield={self.dividend_yield}, market_cap={self.market_cap}, institutional_ownership={self.institutional_ownership}, "
            f"beta={self.beta}, debt_to_equity={self.debt_to_equity}, price_to_book={self.price_to_book})")