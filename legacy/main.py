from analysis import fetch_fundamentals, fetch_historical_data, fetch_news_data
from analysis import analyze_fundamentals, analyze_sentiment, analyze_trend
from strategy.signal_generator import generate_trading_signal

# Assuming you have functions to collect or calculate each analysis
trend_analysis = analyze_trend('AMD')
sentiment_analysis = analyze_sentiment('AMD')
fundamental_analysis = analyze_fundamentals('AMD')

# Generate trading signal based on analysis
signal, strength = generate_trading_signal(trend_analysis, sentiment_analysis, fundamental_analysis)
print(f"Trading Signal: {signal.capitalize()} (Strength: {strength})")