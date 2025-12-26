# Data Services Guide

The data services layer provides a unified interface for fetching sentiment content from multiple sources. Sources can return either raw content (needs scoring) or pre-scored content.

## Overview

### Architecture

```
BaseSentimentSource (abstract)
├─ RawSentimentSource → Returns raw content needing sentiment scoring
│   └─ BingNewsRSSSource
│
└─ ScoredSentimentSource → Returns pre-scored content
    └─ AlphaVantageNewsSource
```

## Quick Start

### Fetching Pre-Scored Content (Alpha Vantage)

```python
from sentiment_analysis_agent.data_services import AlphaVantageNewsSource

# Initialize source (uses mocks by default)
source = AlphaVantageNewsSource(use_mock=True)

# Fetch latest news with string-based time horizon
results = await source.fetch_latest("AAPL", horizon="medium", limit=10)

# Results are SentimentContentScore objects
for item in results:
    print(f"Title: {item.content.title}")
    print(f"Sentiment: {item.sentiment_score}")  # -1 to 1
    print(f"Relevance: {item.relevance_score}")  # 0 to 1
    print(f"Impact: {item.impact_score}")  # 0 to 1
```

### Fetching Raw Content (Bing News RSS)

```python
from sentiment_analysis_agent.data_services import BingNewsRSSSource

# Initialize source
source = BingNewsRSSSource()

# Fetch latest news
results = await source.fetch_latest("AAPL", horizon="short", limit=5)

# Results are SentimentContent objects (not scored yet)
for item in results:
    print(f"Title: {item.title}")
    print(f"URL: {item.url}")
    print(f"Published: {item.published_at}")
    # No sentiment scores - needs to be scored by sentiment pipeline
```

## Time Horizons

All sources support flexible time horizon specification:

```python
# Using TimeWindow enum
from sentiment_analysis_agent.models.sentiment_analysis_models import TimeWindow
results = await source.fetch_latest("AAPL", horizon=TimeWindow.MEDIUM_TERM)

# Using strings (recommended for agents)
results = await source.fetch_latest("AAPL", horizon="short")    # 7 days
results = await source.fetch_latest("AAPL", horizon="medium")   # 30 days
results = await source.fetch_latest("AAPL", horizon="long")     # 90 days

# Alternative string formats (all work)
results = await source.fetch_latest("AAPL", horizon="short term")
results = await source.fetch_latest("AAPL", horizon="MEDIUM-TERM")
```

## Available Sources

### Alpha Vantage News Sentiment

**Type:** Pre-scored  
**Returns:** `list[SentimentContentScore]`

Features:
- Pre-scored sentiment, relevance, and impact scores
- High-quality financial news
- Mock data available for development
- Requires API key for production use

```python
source = AlphaVantageNewsSource(
    api_key="YOUR_API_KEY",  # Optional, defaults to env var
    use_mock=False  # Set False for production
)
```

### Bing News RSS Feed

**Type:** Raw content  
**Returns:** `list[SentimentContent]`

Features:
- Recent news headlines
- Fast and free
- Returns 10-15 items typically
- No API key required

Limitations:
- Bing limits RSS feeds to prevent scraping (typically 10-15 items)
- Best used as supplementary source alongside Alpha Vantage

```python
source = BingNewsRSSSource()
```

## Method Reference

### fetch_latest()

Fetch latest content using categorical time window.

**Parameters:**
- `ticker` (str): Stock ticker symbol (e.g., "AAPL")
- `horizon` (TimeWindow | str): Time window - "short", "medium", or "long"
- `limit` (int | None): Maximum items to return

**Returns:**
- `RawSentimentSource`: `list[SentimentContent]`
- `ScoredSentimentSource`: `list[SentimentContentScore]`

### fetch()

Fetch content with explicit time range.

**Parameters:**
- `ticker` (str): Stock ticker symbol
- `start_time` (datetime): Start of time window (UTC)
- `end_time` (datetime): End of time window (UTC)
- `limit` (int | None): Maximum items to return

**Returns:**
- Same as `fetch_latest()`

## Content Models

### SentimentContent (Raw)

```python
content = SentimentContent(
    content_id="auto_generated",  # Auto-generated hash
    ticker="AAPL",
    source="bing_news",
    title="Apple announces new product",
    summary="Short summary...",
    url="https://example.com/article",
    published_at=datetime(...),
    source_type=SourceType.NEWS,
)
```

### SentimentContentScore (Pre-scored)

```python
scored = SentimentContentScore(
    content=content,  # SentimentContent object
    sentiment_score=0.5,  # -1 (bearish) to 1 (bullish)
    relevance_score=0.8,  # 0 (not relevant) to 1 (highly relevant)
    impact_score=0.6,  # 0 (no impact) to 1 (high impact)
    reasoning="Positive product announcement",
    scored_at=datetime(...),
    model_name="alpha_vantage_news_sentiment",
)
```

## Configuration

Configuration is managed via environment variables or direct parameters:

```bash
# .env file
ALPHA_VANTAGE_API_KEY=your_api_key_here
USE_MOCKS=true  # Defaults to true
```

```python
from sentiment_analysis_agent.config import USE_MOCKS, ALPHA_VANTAGE_API_KEY

# Check configuration
print(f"Using mocks: {USE_MOCKS}")
print(f"API key set: {bool(ALPHA_VANTAGE_API_KEY)}")
```

## Best Practices

### 1. Combine Multiple Sources

Use both Alpha Vantage (pre-scored, high quality) and Bing News (supplementary, recent headlines):

```python
av_source = AlphaVantageNewsSource()
bing_source = BingNewsRSSSource()

# Fetch from both
av_results = await av_source.fetch_latest("AAPL", horizon="medium", limit=20)
bing_results = await bing_source.fetch_latest("AAPL", horizon="short", limit=10)

# av_results are already scored
# bing_results need to be scored by sentiment pipeline
```

### 2. Handle Time Zones Properly

All timestamps are UTC:

```python
from datetime import datetime, timezone

# Correct
now = datetime.now(timezone.utc)
results = await source.fetch("AAPL", start_time=now - timedelta(days=7), end_time=now)

# The models will auto-convert to UTC if timezone is missing
```

### 3. Use String Horizons for Agent-Friendly APIs

```python
# Recommended for LLM/agent integration
horizon = "medium"  # Simple string
results = await source.fetch_latest("AAPL", horizon=horizon)
```

### 4. Content Deduplication

Content IDs are auto-generated based on ticker, source, URL, and published date:

```python
# Same article from different fetches will have same content_id
content1 = await source.fetch_latest("AAPL", horizon="short")
content2 = await source.fetch_latest("AAPL", horizon="short")

# Can deduplicate by content_id
unique_items = {item.content_id: item for item in content1 + content2}.values()
```

## Testing

Simple tests with mock data:

```python
import asyncio
from sentiment_analysis_agent.data_services import AlphaVantageNewsSource

async def test():
    source = AlphaVantageNewsSource(use_mock=True)
    results = await source.fetch_latest("AAPL", horizon="medium", limit=5)
    print(f"Fetched {len(results)} items")
    for item in results:
        print(f"  {item.content.title}")

asyncio.run(test())
```

## Error Handling

```python
import httpx

try:
    results = await source.fetch_latest("AAPL", horizon="short")
except httpx.HTTPError as e:
    print(f"Network error: {e}")
except ValueError as e:
    print(f"Invalid input: {e}")
```

## Next Steps

- See [API Reference](../api/data-services.md) for detailed class documentation
- See [Configuration Reference](../reference/configuration.md) for configuration options
- Implement sentiment scoring pipeline for raw content
- Build aggregation tools to process scored content
