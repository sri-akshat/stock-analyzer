import requests
from bs4 import BeautifulSoup

def fetch_news_data(ticker, limit=10):
  """
  Fetches recent news articles related to the specified ticker.

  Args:
      ticker (str): Stock ticker symbol (e.g., 'AMD').
      limit (int): Maximum number of news articles to fetch.

  Returns:
      list: A list of dictionaries containing 'title', 'date_time', and 'link' for each article.
  """
  url = f"https://finviz.com/quote.ashx?t={ticker}"
  headers = {"User-Agent": "Mozilla/5.0"}
  response = requests.get(url, headers=headers)
  news_data = []

  if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    news_table = soup.find("table", {"class": "fullview-news-outer"})

    if news_table:
      for row in news_table.find_all("tr")[:limit]:
        timestamp = row.td.text.strip()
        title_cell = row.find_all("td")[1]
        title = title_cell.a.text.strip()
        link = title_cell.a["href"]
        news_data.append({"title": title, "date_time": timestamp, "link": link})

  return news_data