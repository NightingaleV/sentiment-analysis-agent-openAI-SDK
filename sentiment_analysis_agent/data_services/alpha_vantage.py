"""Alpha Vantage News Sentiment API data source."""

from datetime import datetime, timezone

import httpx

from sentiment_analysis_agent.config import ALPHA_VANTAGE_API_KEY, USE_MOCKS
from sentiment_analysis_agent.data_services.base import ScoredSentimentSource
from sentiment_analysis_agent.data_services.mocks.alpha_vantage_mock import MOCK_NEWS_SENTIMENT_RESPONSE
from sentiment_analysis_agent.models.sentiment_analysis_models import (
    SentimentContent,
    SentimentContentScore,
    SourceType,
)


class AlphaVantageNewsSource(ScoredSentimentSource):
    """Alpha Vantage News Sentiment API data source.

    Fetches pre-scored news articles with sentiment and relevance scores.
    Supports both real API calls and mock data for development/testing.
    """

    BASE_URL = "https://www.alphavantage.co/query"
    DEFAULT_LIMIT = 50

    def __init__(self, api_key: str | None = None, use_mock: bool | None = None):
        """Initialize Alpha Vantage news source.

        Args:
            api_key: Alpha Vantage API key (defaults to config.ALPHA_VANTAGE_API_KEY)
            use_mock: If True, use mock data instead of real API calls (defaults to config.USE_MOCKS)
        """
        self.api_key = api_key or ALPHA_VANTAGE_API_KEY
        self.use_mock = use_mock if use_mock is not None else USE_MOCKS

        if not self.use_mock and not self.api_key:
            raise ValueError("Alpha Vantage API key is required unless use_mock=True")

    @property
    def source_name(self) -> str:
        """Return source identifier."""
        return "alpha_vantage"

    async def fetch(
        self, ticker: str, start_time: datetime, end_time: datetime, limit: int | None = None
    ) -> list[SentimentContentScore]:
        """Fetch pre-scored news articles from Alpha Vantage.

        Args:
            ticker: Stock ticker symbol
            start_time: Start of time window (UTC)
            end_time: End of time window (UTC)
            limit: Maximum number of items to return

        Returns:
            List of pre-scored sentiment content items
        """
        ticker = ticker.strip().upper()
        limit = limit or self.DEFAULT_LIMIT

        # Get raw response (mock or real)
        if self.use_mock:
            raw_data = MOCK_NEWS_SENTIMENT_RESPONSE
        else:
            raw_data = await self._fetch_from_api(ticker, start_time, end_time)

        # Parse and filter
        scored_items = self._parse_response(raw_data, ticker, start_time, end_time)

        # Sort by relevance score (descending) and apply limit
        scored_items.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_items[:limit] if limit else scored_items

    async def _fetch_from_api(self, ticker: str, start_time: datetime, end_time: datetime) -> dict:
        """Fetch data from Alpha Vantage API.

        Args:
            ticker: Stock ticker symbol
            start_time: Start time (UTC)
            end_time: End time (UTC)

        Returns:
            Raw JSON response from API

        Raises:
            httpx.HTTPError: If request fails
        """
        # Format time_from and time_to as YYYYMMDDTHHMM
        time_from = start_time.strftime("%Y%m%dT%H%M")
        time_to = end_time.strftime("%Y%m%dT%H%M")

        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "time_from": time_from,
            "time_to": time_to,
            "sort": "RELEVANCE",
            "limit": 1000,  # API max, we'll filter later
            "apikey": self.api_key,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()

    def _parse_response(
        self, raw_data: dict, ticker: str, start_time: datetime, end_time: datetime
    ) -> list[SentimentContentScore]:
        """Parse Alpha Vantage response into SentimentContentScore objects.

        Args:
            raw_data: Raw API response
            ticker: Target ticker symbol
            start_time: Filter start time
            end_time: Filter end time

        Returns:
            List of parsed and filtered sentiment content scores
        """
        scored_items: list[SentimentContentScore] = []
        collected_at = datetime.now(timezone.utc)

        for article in raw_data.get("feed", []):
            # Parse published timestamp
            time_published_str = article.get("time_published", "")
            published_at = self._parse_timestamp(time_published_str)

            # Filter by time window
            if published_at and (published_at < start_time or published_at > end_time):
                continue

            # Extract ticker-specific sentiment
            ticker_sentiment = self._extract_ticker_sentiment(article, ticker)
            if not ticker_sentiment:
                continue

            # Build content object (content_id will be auto-generated)
            content = SentimentContent(
                ticker=ticker,
                source=self.source_name,
                title=article.get("title", ""),
                summary=article.get("summary"),
                body=None,  # Alpha Vantage doesn't provide full body
                url=article.get("url"),
                published_at=published_at,
                collected_at=collected_at,
                source_url=article.get("url"),
                source_type=SourceType.NEWS,
                metadata={
                    "authors": ",".join(article.get("authors", [])),
                    "source_domain": article.get("source_domain", ""),
                    "category": article.get("category_within_source", ""),
                    "overall_sentiment_label": article.get("overall_sentiment_label", ""),
                },
            )

            # Build score object
            sentiment_score = float(ticker_sentiment.get("ticker_sentiment_score", 0))
            relevance_score = float(ticker_sentiment.get("relevance_score", 0))

            # Alpha Vantage doesn't provide impact score directly
            # Use relevance as proxy (can be refined later)
            impact_score = relevance_score * 0.8  # Conservative estimate

            scored_item = SentimentContentScore(
                content=content,
                sentiment_score=max(-1.0, min(1.0, sentiment_score)),  # Clamp to [-1, 1]
                impact_score=max(0.0, min(1.0, impact_score)),  # Clamp to [0, 1]
                relevance_score=max(0.0, min(1.0, relevance_score)),  # Clamp to [0, 1]
                confidence=None,  # Not provided by Alpha Vantage
                reasoning=f"Alpha Vantage sentiment: {ticker_sentiment.get('ticker_sentiment_label', 'Unknown')}",
                scored_at=collected_at,
                model_name="alpha_vantage_news_sentiment",
            )

            scored_items.append(scored_item)

        return scored_items

    def _extract_ticker_sentiment(self, article: dict, ticker: str) -> dict | None:
        """Extract sentiment data for a specific ticker from article.

        Args:
            article: Article data from API
            ticker: Target ticker symbol

        Returns:
            Ticker sentiment dict or None if not found
        """
        ticker_sentiments = article.get("ticker_sentiment", [])
        for ts in ticker_sentiments:
            if ts.get("ticker", "").upper() == ticker.upper():
                return ts
        return None

    def _parse_timestamp(self, timestamp_str: str) -> datetime | None:
        """Parse Alpha Vantage timestamp format (YYYYMMDDTHHMM).

        Args:
            timestamp_str: Timestamp string from API

        Returns:
            Parsed datetime (UTC) or None if parsing fails
        """
        if not timestamp_str or timestamp_str == "NULL":
            return None

        try:
            # Format: 20251219T093546
            dt = datetime.strptime(timestamp_str, "%Y%m%dT%H%M%S")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                # Try without seconds
                dt = datetime.strptime(timestamp_str, "%Y%m%dT%H%M")
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                return None
