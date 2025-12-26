# API Reference

Detailed API documentation for sentiment analysis data services.

## Base Classes

### BaseSentimentSource

::: sentiment_analysis_agent.data_services.base.BaseSentimentSource
    options:
      show_source: false
      members:
        - source_name
        - returns_scored
        - fetch
        - fetch_latest

### RawSentimentSource

::: sentiment_analysis_agent.data_services.base.RawSentimentSource
    options:
      show_source: false
      members:
        - returns_scored
        - fetch
        - fetch_latest

### ScoredSentimentSource

::: sentiment_analysis_agent.data_services.base.ScoredSentimentSource
    options:
      show_source: false
      members:
        - returns_scored
        - fetch
        - fetch_latest

## Data Source Implementations

### AlphaVantageNewsSource

::: sentiment_analysis_agent.data_services.alpha_vantage.AlphaVantageNewsSource
    options:
      show_source: false
      members:
        - __init__
        - source_name
        - fetch
        - fetch_latest

### BingNewsRSSSource

::: sentiment_analysis_agent.data_services.bing_news.BingNewsRSSSource
    options:
      show_source: false
      members:
        - __init__
        - source_name
        - fetch
        - fetch_latest
