"""Base interface for sentiment data sources."""

from abc import ABC, abstractmethod
from datetime import datetime

from sentiment_analysis_agent.models.sentiment_analysis_models import (
    SentimentContent,
    SentimentContentScore,
    TimeWindow,
)


class BaseSentimentSource(ABC):
    """Abstract base class for sentiment data sources.

    All data sources must implement this interface to ensure consistency
    across different providers (Alpha Vantage, Bing News, RSS feeds, etc.).
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for the data source.

        Returns:
            Lowercase identifier (e.g., 'alpha_vantage', 'bing_news')
        """
        pass

    @property
    @abstractmethod
    def returns_scored(self) -> bool:
        """Indicates if this source provides pre-scored sentiment data.

        Returns:
            True if source returns SentimentContentScore (pre-scored)
            False if source returns only SentimentContent (needs scoring)
        """
        pass

    @abstractmethod
    async def fetch(
        self, ticker: str, start_time: datetime, end_time: datetime, limit: int | None = None
    ) -> list[SentimentContent] | list[SentimentContentScore]:
        """Fetch sentiment content for a ticker within a time window.

        Args:
            ticker: Stock ticker symbol (will be normalized to uppercase)
            start_time: Start of time window (UTC)
            end_time: End of time window (UTC)
            limit: Maximum number of items to return (None = no limit)

        Returns:
            List of SentimentContent (raw) or SentimentContentScore (pre-scored)

        Raises:
            ValueError: If ticker is invalid or time window is malformed
            httpx.HTTPError: If network request fails
        """
        pass

    async def fetch_latest(
        self, ticker: str, horizon: TimeWindow | str = TimeWindow.SHORT_TERM, limit: int | None = None
    ) -> list[SentimentContent] | list[SentimentContentScore]:
        """Fetch latest sentiment content using TimeWindow horizon.

        Args:
            ticker: Stock ticker symbol (will be normalized to uppercase)
            horizon: Time horizon - can be TimeWindow enum or string ('short', 'medium', 'long')
            limit: Maximum number of items to return (None = no limit)

        Returns:
            List of SentimentContent (raw) or SentimentContentScore (pre-scored)
        """
        # Convert string to TimeWindow if needed
        if isinstance(horizon, str):
            horizon = TimeWindow(horizon)

        start_time, end_time = horizon.to_time_range()
        return await self.fetch(ticker, start_time, end_time, limit)


class RawSentimentSource(BaseSentimentSource):
    """Base class for sources that return raw content only (needs scoring)."""

    @property
    def returns_scored(self) -> bool:
        """Raw sources always return False."""
        return False

    @abstractmethod
    async def fetch(
        self, ticker: str, start_time: datetime, end_time: datetime, limit: int | None = None
    ) -> list[SentimentContent]:
        """Fetch raw sentiment content."""
        pass


class ScoredSentimentSource(BaseSentimentSource):
    """Base class for sources that return pre-scored content."""

    @property
    def returns_scored(self) -> bool:
        """Scored sources always return True."""
        return True

    @abstractmethod
    async def fetch(
        self, ticker: str, start_time: datetime, end_time: datetime, limit: int | None = None
    ) -> list[SentimentContentScore]:
        """Fetch pre-scored sentiment content."""
        pass
