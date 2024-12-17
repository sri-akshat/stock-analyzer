import yfinance as yf
import requests
import asyncio
from bs4 import BeautifulSoup
from newspaper import Article
from sentence_transformers import SentenceTransformer
from statistics import mean
from sec_api import QueryApi
import faiss
import numpy as np

# Configurable parameters for stabilization
SUPPORT_LEVELS = [132, 112]  # Recent support levels
STABILIZING_MINUTES = 100  # Number of consecutive minutes to check stability near support level
TOLERANCE = 0.5  # Percentage tolerance for support level stability

# Initialize the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# api keys
FINHUB_API_KEY = 'csir2l1r01qt46e82fp0csir2l1r01qt46e82fpg'
FRED_API_KEY = '19b2644b5289ed570d208fa66035ca24'

# Detect dynamic support levels based on recent lows
def detect_dynamic_support_levels(stock_data, window=20, threshold=0.01):
  recent_lows = stock_data['Close'].rolling(window=window).min().dropna()
  avg_low = mean(recent_lows[-window:])
  dynamic_support_levels = [level for level in recent_lows if abs(level - avg_low) / avg_low < threshold]
  return list(set(dynamic_support_levels))

# Fetch latest news from Finviz
def fetch_latest_news_finviz(ticker, limit=10):
  url = f"https://finviz.com/quote.ashx?t={ticker}"
  headers = {"User-Agent": "Mozilla/5.0"}
  response = requests.get(url, headers=headers)
  if response.status_code != 200:
    print(f"Failed to retrieve page for {ticker} (status code: {response.status_code})")
    return []

  soup = BeautifulSoup(response.text, "html.parser")
  news_table = soup.find("table", {"class": "fullview-news-outer"})
  articles = []
  if news_table:
    for row in news_table.find_all("tr")[:limit]:
      timestamp = row.td.text.strip()
      title_cell = row.find_all("td")[1]
      title = title_cell.a.text.strip()
      link = title_cell.a["href"]
      articles.append({"title": title, "url": link, "publishedAt": timestamp})
  return articles

# Fetch full article content using newspaper3k
async def fetch_full_content_async(url):
  try:
    article = Article(url)
    article.download()
    article.parse()
    content = article.text[:3000]
    return content
  except Exception as e:
    print(f"Failed to fetch content from {url}: {e}")
    return "Failed to fetch content."

# Run async fetch for all articles
async def fetch_articles_content(ticker, limit=10):
  articles = fetch_latest_news_finviz(ticker, limit)
  tasks = [fetch_full_content_async(article['url']) for article in articles]
  full_texts = await asyncio.gather(*tasks)
  documents = [
      {
          'title': articles[i]['title'],
          'content': full_texts[i],
          'publishedAt': articles[i]['publishedAt'],
      }
      for i in range(len(articles))
  ]
  return documents

def fetch_minute_data(ticker, interval="1m", period="1d"):
  """
  Fetch minute-by-minute price data for a given stock ticker over a specified period.
  :param ticker: Stock ticker symbol as a string (e.g., "AMD").
  :param interval: Data interval (e.g., "1m" for 1-minute intervals).
  :param period: Total period to fetch (e.g., "1d" for one day).
  :return: DataFrame with the minute-by-minute price data.
  """
  stock = yf.Ticker(ticker)
  data = stock.history(period=period, interval=interval)
  return data

# Fetch technical data and additional market data
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

# Fetch options data for open interest and put/call ratios
def fetch_options_data(ticker):
  stock = yf.Ticker(ticker)
  options_dates = stock.options
  if options_dates:
    options = stock.option_chain(options_dates[0])
    calls_open_interest = options.calls['openInterest'].sum()
    puts_open_interest = options.puts['openInterest'].sum()
    put_call_ratio = puts_open_interest / calls_open_interest if calls_open_interest != 0 else None

    return {
        "calls_open_interest": calls_open_interest,
        "puts_open_interest": puts_open_interest,
        "put_call_ratio": put_call_ratio
    }
  return None

# Fetch institutional holdings and insider activity (example API)
def fetch_institutional_holdings(ticker):
  url = f"https://finnhub.io/api/v1/stock/ownership?symbol={ticker}&token={FINHUB_API_KEY}"
  response = requests.get(url)
  if response.status_code == 200:
    return response.json()
  return None

def fetch_institutional_holdings_fmp(ticker):
  api_key = "fGnVWQVRsPQbjNmEAHa97dSMhohpmCzQ"
  url = f"https://financialmodelingprep.com/api/v3/institutional-holder/{ticker}?apikey={api_key}"
  response = requests.get(url)
  if response.status_code == 200:
    return response.json()
  else:
    print(f"Failed to retrieve data - {response}")
    return None

def fetch_institutional_holdings_sec(ticker):
  # Initialize the QueryApi with your sec-api.io API key
  api_key = "abaf4774e92aba3591c423c8ae115c6ca5c4c8a053f15aef4da076beaee924f2"  # Replace with your actual sec-api.io API key
  query_api = QueryApi(api_key=api_key)

  # Define the query to fetch 13F filings for the specified ticker
  query = {
      "query": f'formType:"13F" AND holdings.ticker:{ticker}',
      "from": "0",
      "size": "10",  # Number of filings to retrieve
      "sort": [{"filedAt": {"order": "desc"}}]
  }

  # Fetch the filings
  try:
    filings = query_api.get_filings(query)
  except Exception as e:
    print(f"Error fetching data: {e}")
    return []

  # Check if data was returned
  if not filings or 'filings' not in filings:
    print("No filings data returned.")
    return []

  # Process and filter holdings for the specified ticker
  holdings_data = []
  for filing in filings.get('filings', []):
    filing_data = {
        "filing_date": filing['filedAt'],
        "holdings": []
    }
    print(f"Processing Filing Date: {filing['filedAt']}")

    # Only include holdings that match the ticker
    if 'holdings' in filing:
      for holding in filing['holdings']:
        if holding.get("ticker") == ticker:  # Filter for AMD only
          holding_info = {
              "issuer": holding.get("nameOfIssuer"),
              "class_title": holding.get("titleOfClass"),
              "cusip": holding.get("cusip"),
              "value_usd": holding.get("value"),
              "shares": holding.get("sshPrnamt"),
              "investment_discretion": holding.get("investmentDiscretion"),
              "voting_authority": holding.get("votingAuthority", {}).get("Sole", 0)
          }
          filing_data["holdings"].append(holding_info)
    else:
      print(f"No holdings data found for filing on {filing['filedAt']}.")

    # Only add to holdings_data if we have relevant holdings
    if filing_data["holdings"]:
      holdings_data.append(filing_data)

  if not holdings_data:
    print("No holdings data available.")
  return holdings_data

# Fetch short interest data
def fetch_short_interest(ticker):
  url = f"https://finnhub.io/api/v1/stock/short-interest?symbol={ticker}&token={FINHUB_API_KEY}"
  response = requests.get(url)
  if response.status_code == 200:
    return response.json()
  return None

def fetch_short_interest_alpha_vantage(ticker):
  api_key = "00X7KSIC3V1XLQOD"
  url = f"https://www.alphavantage.co/query?function=SHORT_INTEREST&symbol={ticker}&apikey={api_key}"
  response = requests.get(url)
  if response.status_code == 200:
    data = response.json()
    return data
  else:
    print(f"Error: {response.status_code}")
    return None

def fetch_short_interest(ticker):
  api_key = '5cdb0ff8c113498ea3075ea8483c59d1'
  url = f"https://api.twelvedata.com/statistics?symbol={ticker}&apikey={api_key}"
  response = requests.get(url)

  if response.status_code == 200:
    data = response.json()
    if 'statistics' in data and 'stock_statistics' in data['statistics']:
      stock_stats = data['statistics']['stock_statistics']
      short_interest = stock_stats.get('shares_short', 'Data not available')
      short_ratio = stock_stats.get('short_ratio', 'Data not available')
      short_percent_of_shares_outstanding = stock_stats.get('short_percent_of_shares_outstanding', 'Data not available')

      return {
          'short_interest': short_interest,
          'short_ratio': short_ratio,
          'short_percent_of_shares_outstanding': short_percent_of_shares_outstanding
      }
    else:
      print("Short interest data not found in the response.")
      return None
  else:
    print(f"Failed to retrieve data - Status code: {response.status_code}")
    return None

# Fetch macro data for interest rates
def fetch_macro_data():
  from fredapi import Fred
  fred = Fred(api_key=FRED_API_KEY)
  interest_rates = fred.get_series('DFF')  # Federal Funds Rate
  return interest_rates.tail()

# Check stability near support levels
def check_stability_near_support(stock_data, support_level):
  close_prices = stock_data['Close'].values
  consecutive_minutes_near_support = 0

  for price in close_prices:
    if support_level * (1 - TOLERANCE / 100) <= price <= support_level * (1 + TOLERANCE / 100):
      consecutive_minutes_near_support += 1
      if consecutive_minutes_near_support >= STABILIZING_MINUTES:
        return True
    else:
      consecutive_minutes_near_support = 0  # Reset if price moves away from support level
  return False

# Monitor dynamic support levels
def monitor_dynamic_support_levels(ticker):
  stock_data = fetch_minute_data(ticker, "1m", "5d")
  potential_support_levels = detect_dynamic_support_levels(stock_data)
  print("Potential dynamic support levels:", potential_support_levels)

  stable_levels = []
  for level in potential_support_levels:
    if check_stability_near_support(stock_data, level):
      stable_levels.append(level)

  if stable_levels:
    print(f"Stock is stabilizing near support levels: {stable_levels}")
  else:
    print("No stabilization near dynamic support levels yet.")
  return stable_levels if stable_levels else "No stabilization near dynamic support levels yet."

# Generate prompt with additional data
def generate_prompt(ticker, user_query):
  documents = asyncio.run(fetch_articles_content(ticker, 10))
  technicals = fetch_technical_data(ticker)
  options_data = fetch_options_data(ticker)
  institutional_holdings = fetch_institutional_holdings_sec(ticker)
  short_interest = fetch_short_interest(ticker)
  interest_rates = fetch_macro_data()

  # Monitor stability near support levels
  stability_text = "No stabilization near support levels yet."
  stable_levels = monitor_dynamic_support_levels(ticker)
  if stable_levels:
    stability_text = f"{ticker} is stabilizing near support levels: {stable_levels}"

  # Prepare context from the articles
  context = "\n\n".join([
      f"Title: {doc['title']}\nPublished At: {doc['publishedAt']}\nContent: {doc['content']}"
      for doc in documents
  ])

  # Add technical data to the context
  technicals_text = (
      f"Current Price: {technicals['current_price']}\n"
      f"52-Week High: {technicals['fifty_two_week_high']}\n"
      f"52-Week Low: {technicals['fifty_two_week_low']}\n"
      f"50-Day Moving Average: {technicals['moving_average_50']}\n"
      f"200-Day Moving Average: {technicals['moving_average_200']}\n"
      f"Trading Volume: {technicals['volume']}\n"
      f"Average Volume: {technicals['average_volume']}\n"
  )

  # Add options, institutional holdings, short interest, and macro data
  options_text = (
      f"Calls Open Interest: {options_data['calls_open_interest']}\n"
      f"Puts Open Interest: {options_data['puts_open_interest']}\n"
      f"Put/Call Ratio: {options_data['put_call_ratio']}"
  ) if options_data else "Options Data: Unavailable"

  holdings_text = f"Institutional Holdings: {institutional_holdings}" if institutional_holdings else "Institutional Holdings: Unavailable"
  short_interest_text = f"Short Interest: {short_interest}" if short_interest else "Short Interest: Unavailable"
  macro_text = f"Interest Rates: {interest_rates.values.tolist()}" if interest_rates is not None else "Interest Rates: Unavailable"

  # Construct the final prompt with all data, including stability_text
  prompt = (
      "System: You are a financial analysis assistant that provides stock recommendations based on recent news, "
      "trends, technical analysis, and price stabilization checks.\n\n"
      f"User: {user_query}\n\n"
      f"Technical Data:\n{technicals_text}\n\n"
      f"Stabilization Info:\n{stability_text}\n\n"
      f"Options Data:\n{options_text}\n\n"
      f"Institutional Holdings:\n{holdings_text}\n\n"
      f"Short Interest:\n{short_interest_text}\n\n"
      f"Macro Data:\n{macro_text}\n\n"
      f"Articles:\n{context}"
  )

  print("\nGenerated Prompt:")
  print(prompt)
  return prompt


# Define the ticker symbol and the user query
ticker = "AMD"
user_query = "Is it a good time to buy AMD stock given recent news and technical data?"

# Call the generate_prompt function to create a structured prompt for analysis
prompt = generate_prompt(ticker, user_query)
# #
# Print the generated prompt
print("\nGenerated Analysis Prompt:")
print(prompt)

# print(monitor_dynamic_support_levels(ticker))

# - add VIX