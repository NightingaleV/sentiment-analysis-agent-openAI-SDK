"""Data source layer for sentiment analysis."""

from sentiment_analysis_agent.data_services.alpha_vantage import AlphaVantageNewsSource
from sentiment_analysis_agent.data_services.base import BaseSentimentSource, RawSentimentSource, ScoredSentimentSource
from sentiment_analysis_agent.data_services.bing_news import BingNewsRSSSource

__all__ = [
    "BaseSentimentSource",
    "RawSentimentSource",
    "ScoredSentimentSource",
    "AlphaVantageNewsSource",
    "BingNewsRSSSource",
]
