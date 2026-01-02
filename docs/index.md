# Sentiment Analysis Agent Documentation

Welcome to the Sentiment Analysis Agent documentation. This project provides AI-powered sentiment analysis of stock market news from multiple sources.

## Quick Links

### Guides
- [Data Services Guide](guides/data-services.md) - Learn how to fetch sentiment content from various sources

### API Reference
- [Data Services API](api/data-services.md) - Detailed API documentation for data services

### Reference
- [Configuration](reference/configuration.md) - Environment variables and configuration options
- Development guidelines (see [AGENTS.md](../AGENTS.md))

## Getting Started

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd sentiment-analysis-agent

# Install dependencies with uv
uv sync

# Install development dependencies
uv sync --group dev
```

### Quick Example

```python
from sentiment_analysis_agent.data_services import AlphaVantageNewsSource

# Initialize source with mock data
source = AlphaVantageNewsSource(use_mock=True)

# Fetch latest news
results = await source.fetch_latest("AAPL", horizon="medium", limit=10)

# Process results
for item in results:
    print(f"{item.content.title}: {item.sentiment_score}")
```

## Project Structure

```
sentiment-analysis-agent/
├── sentiment_analysis_agent/
│   ├── data_services/      # Data source implementations
│   ├── models/             # Pydantic data models
│   ├── agents/             # Agent implementations (future)
│   └── config.py           # Configuration
├── tests/                  # Test suite
├── docs/                   # Documentation (you are here)
└── pyproject.toml         # Project configuration
```

## Documentation Structure

### Guides (`/guides`)
User-focused how-to guides and tutorials for working with the system.

### API Reference (`/api`)
Auto-generated API documentation using mkdocstrings for detailed class and method reference.

### Reference (`/reference`)
Technical reference materials including configuration options, environment variables, and architectural decisions.

## Key Concepts

### Data Services
Data services provide a unified interface for fetching sentiment content:
- **Raw Sources**: Return unscored content that needs sentiment analysis (e.g., Bing News RSS)
- **Scored Sources**: Return pre-scored content with sentiment/relevance/impact scores (e.g., Alpha Vantage)

### Time Horizons
All sources support flexible time windows:
- `"short"` - 7 days
- `"medium"` - 30 days
- `"long"` - 90 days

### Content Models
- **SentimentContent**: Raw content item (title, URL, summary, etc.)
- **SentimentContentScored**: Scored content with sentiment/relevance/impact metrics

## Development

See [AGENTS.md](../AGENTS.md) for development guidelines and coding standards.

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_bing_news.py

# Run with coverage
uv run pytest --cov=sentiment_analysis_agent
```

### Code Formatting

```bash
uv run black --line-length 120 sentiment_analysis_agent/
```

## Contributing

This is a learning project exploring different AI agent frameworks. Contributions should follow:
- Python 3.12+ with type hints
- Pydantic models for data validation
- Google-style docstrings
- Conventional commits

## License

[Specify license here]
