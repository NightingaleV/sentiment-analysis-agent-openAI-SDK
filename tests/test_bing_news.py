"""Tests for Bing News RSS feed source."""

import pytest

from sentiment_analysis_agent.data_services import BingNewsRSSSource
from sentiment_analysis_agent.models.sentiment_analysis_models import SourceType


@pytest.mark.asyncio
async def test_bing_news_returns_multiple_items():
    """Test that Bing RSS returns multiple items for long term interval."""
    source = BingNewsRSSSource()
    
    # Fetch with long term horizon (90 days)
    results = await source.fetch_latest("AAPL", horizon="long", limit=20)
    
    # Should get multiple items
    assert len(results) > 1, f"Expected multiple items, got {len(results)}"
    assert len(results) <= 20, f"Expected max 20 items due to limit, got {len(results)}"


@pytest.mark.asyncio
async def test_bing_news_content_structure():
    """Test that returned content has correct structure."""
    source = BingNewsRSSSource()
    
    results = await source.fetch_latest("AAPL", horizon="medium", limit=5)
    
    # Should have at least one item
    assert len(results) >= 1, "Expected at least one item"
    
    # Check first item structure
    first = results[0]
    assert first.ticker == "AAPL"
    assert first.source == "bing_news"
    assert first.source_type == SourceType.NEWS
    assert first.title is not None and len(first.title) > 0
    assert first.url is not None
    assert first.content_id is not None and len(first.content_id) > 0
    assert first.published_at is not None
    assert first.collected_at is not None


@pytest.mark.asyncio
async def test_bing_news_source_properties():
    """Test source properties."""
    source = BingNewsRSSSource()
    
    assert source.source_name == "bing_news"
    assert source.returns_scored is False


@pytest.mark.asyncio
async def test_bing_news_different_tickers():
    """Test fetching news for different tickers."""
    source = BingNewsRSSSource()
    
    # Test with different ticker
    results = await source.fetch_latest("TSLA", horizon="short", limit=5)
    
    # All items should have correct ticker
    for item in results:
        assert item.ticker == "TSLA"


@pytest.mark.asyncio
async def test_bing_news_respects_limit():
    """Test that limit parameter is respected."""
    source = BingNewsRSSSource()
    
    # Request only 3 items
    results = await source.fetch_latest("AAPL", horizon="long", limit=3)
    
    assert len(results) <= 3, f"Expected max 3 items, got {len(results)}"
