from textblob import TextBlob
import nltk

from data_collection import fetch_news_data

nltk.download('punkt')

def analyze_sentiment(ticker):
  """
  Analyze sentiment based on news headlines for the given ticker.

  Parameters:
      ticker (str): Stock ticker symbol (e.g., 'AMD').

  Returns:
      dict: Average polarity and subjectivity scores.
  """
  articles = fetch_news_data(ticker)
  print("Articles Data:", articles)  # Debugging line

  polarities = []
  subjectivities = []

  # Ensure each article has the expected 'title' key
  for article in articles:
    if isinstance(article, dict) and 'title' in article:
      analysis = TextBlob(article['title'])
      polarities.append(analysis.polarity)
      subjectivities.append(analysis.subjectivity)
    else:
      print(f"Unexpected article format: {article}")

  # Calculate average polarity and subjectivity
  average_polarity = sum(polarities) / len(polarities) if polarities else 0
  average_subjectivity = sum(subjectivities) / len(subjectivities) if subjectivities else 0

  sentiment_analysis = {
      'average_polarity': average_polarity,
      'average_subjectivity': average_subjectivity,
  }

  print("Sentiment Analysis:", sentiment_analysis)
  return sentiment_analysis