import requests
from bs4 import BeautifulSoup
from datetime import datetime
from newspaper import Article

def fetch_finviz_news(ticker, limit=10):
  url = f"https://finviz.com/quote.ashx?t={ticker}"
  headers = {"User-Agent": "Mozilla/5.0"}
  response = requests.get(url, headers=headers)

  # Check if the page was fetched successfully
  if response.status_code != 200:
    print(f"Failed to retrieve page for {ticker} (status code: {response.status_code})")
    return []

  soup = BeautifulSoup(response.text, "html.parser")

  # Find the news table
  news_table = soup.find("table", {"class": "fullview-news-outer"})

  # Extract news items
  articles = []
  if news_table:
    for row in news_table.find_all("tr")[:limit]:  # Limit the number of articles
      timestamp = row.td.text.strip()  # This could be just time or date + time
      if " " not in timestamp:  # Add date if missing
        timestamp = f"{datetime.today().date()} {timestamp}"

      title_cell = row.find_all("td")[1]
      title = title_cell.a.text.strip()
      link = title_cell.a["href"]

      articles.append({
          "title": title,
          "url": link,
          "publishedAt": timestamp
      })

  return articles

def fetch_article_content(url):
  try:
    article = Article(url)
    article.download()
    article.parse()
    return article.text[:3000]  # Limit to 3000 characters
  except Exception as e:
    print(f"Failed to fetch content from {url}: {e}")
    return "Content not available."

# def fetch_article_content(url):
#   headers = {"User-Agent": "Mozilla/5.0"}
#   try:
#     response = requests.get(url, headers=headers)
#     response.raise_for_status()
#
#     soup = BeautifulSoup(response.text, "html.parser")
#
#     # Extract article content based on common HTML tags
#     paragraphs = soup.find_all('p')
#     content = "\n".join([p.get_text() for p in paragraphs])
#
#     return content[:3000]  # Limit to 3000 characters for readability
#   except requests.exceptions.RequestException as e:
#     print(f"Failed to fetch content from {url}: {e}")
#     return "Content not available."

# Main function to get articles and their content for a specific ticker
def get_news_with_content(ticker, limit=10):
  print(f"Fetching latest news for {ticker} from Finviz...")
  articles = fetch_finviz_news(ticker, limit=limit)

  print(f"\nFetching full content for each article...")
  for article in articles:
    content = fetch_article_content(article["url"])
    article["content"] = content
    print(f"\nTitle: {article['title']}")
    print(f"Published At: {article['publishedAt']}")
    print(f"URL: {article['url']}")
    print(f"Content:\n{article['content']}\n")

# Example usage
ticker = "AMD"
get_news_with_content(ticker, limit=20)