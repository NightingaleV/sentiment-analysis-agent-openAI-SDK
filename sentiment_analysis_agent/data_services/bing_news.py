"""Bing News RSS feed data source."""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

from sentiment_analysis_agent.data_services.base import RawSentimentSource
from sentiment_analysis_agent.models.sentiment_analysis_models import SentimentContent, SourceType


class BingNewsRSSSource(RawSentimentSource):
    """Bing News RSS feed data source.

    Fetches raw news headlines from Bing News RSS feed.
    Content must be scored separately by sentiment scoring pipeline.

    **Important Limitations:**
    - Bing RSS feeds typically return only 1-10 most recent items
    - Results are limited regardless of time window requested
    - This is an anti-scraping measure by Bing
    - Best used alongside other sources (e.g., Alpha Vantage) for comprehensive coverage
    """

    BASE_URL = "https://www.bing.com/news/search"
    DEFAULT_LIMIT = 50

    def __init__(self):
        """Initialize Bing News RSS source."""
        pass

    @property
    def source_name(self) -> str:
        """Return source identifier."""
        return "bing_news"

    async def fetch(
        self, ticker: str, start_time: datetime, end_time: datetime, limit: int | None = None
    ) -> list[SentimentContent]:
        """Fetch raw news articles from Bing News RSS.

        Args:
            ticker: Stock ticker symbol
            start_time: Start of time window (UTC)
            end_time: End of time window (UTC)
            limit: Maximum number of items to return

        Returns:
            List of raw sentiment content items (not scored)
        """
        ticker = ticker.strip().upper()
        limit = limit or self.DEFAULT_LIMIT

        # Fetch RSS feed
        rss_content = await self._fetch_rss_feed(ticker, start_time, end_time)

        # Parse RSS XML
        content_items = self._parse_rss_feed(rss_content, ticker, start_time, end_time)

        # RSS feed already sorted by date (newest first) due to sortbydate=1
        # Apply limit
        return content_items[:limit] if limit else content_items

    async def _fetch_rss_feed(self, ticker: str, start_time: datetime, end_time: datetime) -> str:
        """Fetch RSS feed from Bing News (browser-like)."""
        time_range_days = (end_time - start_time).days

        if time_range_days <= 1:
            interval = "7"  # past 24h
        elif time_range_days <= 7:
            interval = "8"  # past 7d
        else:
            interval = "9"  # past 30d

        # ✅ IMPORTANT: qft must be UN-encoded. Let httpx encode it.
        qft = f'sortbydate="1"+interval="{interval}"'

        params = {
            "q": ticker,
            "format": "rss",
            "qft": qft,
            # ✅ Force same market/lang as your browser feed (you showed en-us)
            "setmkt": "en-us",
            "setlang": "en-us",
            # Optional: may be ignored / capped by Bing for RSS
            "count": "50",
        }

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
            # ✅ Cookie “warm-up” (often helps make results match browser behavior)
            await client.get("https://www.bing.com/")

            req = client.build_request("GET", self.BASE_URL, params=params)
            print(f"Fetching Bing RSS URL: {req.url}")

            resp = await client.send(req)
            resp.raise_for_status()

            # Debug: count items
            root = ET.fromstring(resp.text)
            items = root.findall("./channel/item")
            print(f"RSS items: {len(items)}")
            return resp.text

    def _parse_rss_feed(
        self, rss_content: str, ticker: str, start_time: datetime, end_time: datetime
    ) -> list[SentimentContent]:
        """Parse RSS XML feed into SentimentContent objects.

        Args:
            rss_content: Raw RSS XML string
            ticker: Target ticker symbol
            start_time: Filter start time
            end_time: Filter end time

        Returns:
            List of parsed and filtered sentiment content items
        """
        content_items: list[SentimentContent] = []
        collected_at = datetime.now(timezone.utc)

        try:
            root = ET.fromstring(rss_content)
            channel = root.find("channel")
            if channel is None:
                return content_items

            for item in channel.findall("item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                description_elem = item.find("description")
                pub_date_elem = item.find("pubDate")

                # Handle namespaced Source element (News:Source)
                # The namespace might vary, so try both namespaced and non-namespaced
                source_elem = item.find("source")
                if source_elem is None:
                    # Try to find any element ending with 'Source'
                    for child in item:
                        if child.tag.endswith("Source"):
                            source_elem = child
                            break

                # Extract data
                title = title_elem.text if title_elem is not None and title_elem.text else ""
                url = link_elem.text if link_elem is not None and link_elem.text else None
                description = description_elem.text if description_elem is not None else None
                source_name = source_elem.text if source_elem is not None and source_elem.text else "Unknown"

                # Parse publication date
                published_at = None
                if pub_date_elem is not None and pub_date_elem.text:
                    try:
                        published_at = parsedate_to_datetime(pub_date_elem.text)
                        # Ensure UTC
                        if published_at.tzinfo is None:
                            published_at = published_at.replace(tzinfo=timezone.utc)
                        else:
                            published_at = published_at.astimezone(timezone.utc)
                    except (ValueError, TypeError):
                        pass

                # Note: Bing already filters by interval, so we don't need strict time filtering
                # Only filter out future dates (which shouldn't happen but good to be safe)
                if published_at and published_at > end_time:
                    continue

                # Skip items without minimum required data
                if not title or not url:
                    continue

                # Build content object (content_id will be auto-generated)
                content = SentimentContent(
                    ticker=ticker,
                    source=self.source_name,
                    title=title,
                    summary=description,
                    body=None,  # RSS doesn't provide full body
                    url=url,
                    published_at=published_at,
                    collected_at=collected_at,
                    source_url=url,
                    source_type=SourceType.NEWS,
                    metadata={"rss_source": source_name},
                )

                content_items.append(content)

        except ET.ParseError as e:
            raise ValueError(f"Failed to parse RSS feed: {e}") from e

        return content_items
