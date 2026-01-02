"""Quick test script for data sources."""

import asyncio
import pytest
from datetime import datetime, timezone

from sentiment_analysis_agent.data_services import (
    AlphaVantageNewsSource,
    BingNewsRSSSource,
)
from sentiment_analysis_agent.models.sentiment_analysis_models import TimeWindow


@pytest.mark.asyncio
async def test_alpha_vantage():
    """Test Alpha Vantage source with mock data."""
    print("\n=== Testing Alpha Vantage Source ===")
    source = AlphaVantageNewsSource(use_mock=True)

    print(f"Source name: {source.source_name}")
    print(f"Returns scored: {source.returns_scored}")

    # Test fetch_latest with string horizon (agent-friendly API)
    results = await source.fetch_latest("AAPL", horizon="medium", limit=5)

    print(f"\nFetched {len(results)} items")
    if results:
        first = results[0]

        type(first)
        print(first)
        print(f"\nFirst item:")
        print(f"  Title: {first.content.title}")
        print(f"  Content ID: {first.content.content_id}")
        print(f"  Ticker: {first.content.ticker}")
        print(f"  Source: {first.content.source}")
        print(f"  URL: {first.content.url}")
        print(f"  Published: {first.content.published_at}")
        print(f"  Sentiment Score: {first.sentiment_score:.3f}")
        print(f"  Relevance Score: {first.relevance_score:.3f}")
        print(f"  Impact Score: {first.impact_score:.3f}")
        print(f"  Reasoning: {first.reasoning}")


@pytest.mark.asyncio
async def test_bing_news():
    """Test Bing News RSS source."""
    print("\n\n=== Testing Bing News RSS Source ===")
    source = BingNewsRSSSource()

    print(f"Source name: {source.source_name}")
    print(f"Returns scored: {source.returns_scored}")

    try:
        # Test fetch_latest with string horizon (agent-friendly API)
        results = await source.fetch_latest("AAPL", horizon="short", limit=5)

        print(f"\nFetched {len(results)} items")
        if results:
            first = results[0]
            print(f"\nFirst item:")
            print(f"  Title: {first.title}")
            print(f"  Content ID: {first.content_id}")
            print(f"  Ticker: {first.ticker}")
            print(f"  Source: {first.source}")
            print(f"  URL: {first.url}")
            print(f"  Published: {first.published_at}")
            print(f"  Summary: {first.summary[:100] if first.summary else 'N/A'}...")
    except Exception as e:
        print(f"\nError fetching Bing News: {e}")
        print("This is expected if there are network issues or rate limiting")


async def main():
    """Run all tests."""
    await test_alpha_vantage()
    await test_bing_news()
    print("\n=== Tests Complete ===\n")


if __name__ == "__main__":
    asyncio.run(main())
