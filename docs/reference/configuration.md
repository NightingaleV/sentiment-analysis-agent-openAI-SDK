# Configuration Reference

This document describes all configuration options for the sentiment analysis agent.

## Environment Variables

### General Configuration

#### `USE_MOCKS`
- **Type**: Boolean (string)
- **Default**: `"true"`
- **Values**: `"true"`, `"false"`, `"1"`, `"0"`, `"yes"`, `"no"`, `"on"`, `"off"`
- **Description**: Toggle mock data usage across all data services
- **Example**: 
  ```bash
  USE_MOCKS=false  # Use real API calls
  USE_MOCKS=true   # Use mock data (default)
  ```

### Data Source API Keys

#### `ALPHA_VANTAGE_API_KEY`
- **Type**: String
- **Default**: None
- **Required**: Only when `USE_MOCKS=false`
- **Description**: API key for Alpha Vantage News Sentiment API
- **Where to get**: [Alpha Vantage API Keys](https://www.alphavantage.co/support/#api-key)
- **Example**:
  ```bash
  ALPHA_VANTAGE_API_KEY=your_api_key_here
  ```

## Configuration File

Configuration is managed through `sentiment_analysis_agent/config.py`:

```python
from sentiment_analysis_agent.config import USE_MOCKS, ALPHA_VANTAGE_API_KEY

# Check current configuration
print(f"Using mocks: {USE_MOCKS}")
print(f"API key configured: {bool(ALPHA_VANTAGE_API_KEY)}")
```

## Development vs Production

### Development Mode (Default)

```bash
# .env or environment
USE_MOCKS=true
```

In development mode:
- All data services use mock data by default
- No API keys required
- Predictable, repeatable results
- Fast execution (no network calls)

### Production Mode

```bash
# .env or environment
USE_MOCKS=false
ALPHA_VANTAGE_API_KEY=your_actual_api_key
```

In production mode:
- Data services make real API calls
- API keys required for external services
- Live data from real sources
- Subject to API rate limits

## Per-Source Configuration

You can override the global `USE_MOCKS` setting for individual sources:

```python
from sentiment_analysis_agent.data_services import AlphaVantageNewsSource

# Force mock data regardless of USE_MOCKS env var
source = AlphaVantageNewsSource(use_mock=True)

# Force real API calls regardless of USE_MOCKS env var
source = AlphaVantageNewsSource(
    api_key="your_key_here",
    use_mock=False
)
```

## Time Window Configuration

Time windows are defined in the `TimeWindow` enum:

| Window | Duration | Use Case |
|--------|----------|----------|
| `SHORT_TERM` | 7 days | Recent news, breaking events |
| `MEDIUM_TERM` | 30 days | Monthly trends, earnings season |
| `LONG_TERM` | 90 days | Quarterly analysis, long-term sentiment |

These can be modified in `sentiment_analysis_agent/models/sentiment_analysis_models.py`:

```python
class TimeWindow(StrEnum):
    SHORT_TERM = "short"   # 7 days
    MEDIUM_TERM = "medium" # 30 days
    LONG_TERM = "long"     # 90 days
    
    def duration(self) -> timedelta:
        if self is TimeWindow.SHORT_TERM:
            return timedelta(days=7)  # Modify here
        if self is TimeWindow.MEDIUM_TERM:
            return timedelta(days=30)  # Modify here
        return timedelta(days=90)  # Modify here
```

## Logging Configuration

Currently, data services use print statements for debugging. Future versions will use Python's logging module:

```python
import logging

# Enable debug logging (future)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("sentiment_analysis_agent")
```

## Best Practices

### 1. Use Environment Files

Create a `.env` file in the project root:

```bash
# .env
USE_MOCKS=true
ALPHA_VANTAGE_API_KEY=your_key_here
```

Load with python-dotenv (future enhancement):

```python
from dotenv import load_dotenv
load_dotenv()
```

### 2. Never Commit API Keys

Add `.env` to `.gitignore`:

```
.env
*.env
.env.*
```

### 3. Use Mock Data in Tests

```python
import pytest
from sentiment_analysis_agent.data_services import AlphaVantageNewsSource

@pytest.fixture
def av_source():
    return AlphaVantageNewsSource(use_mock=True)

def test_fetch_latest(av_source):
    results = await av_source.fetch_latest("AAPL", horizon="short")
    assert len(results) > 0
```

### 4. Validate Configuration on Startup

```python
from sentiment_analysis_agent.config import USE_MOCKS, ALPHA_VANTAGE_API_KEY

if not USE_MOCKS and not ALPHA_VANTAGE_API_KEY:
    raise ValueError("ALPHA_VANTAGE_API_KEY required when USE_MOCKS=false")
```

## Troubleshooting

### "API key is required unless use_mock=True"

**Problem**: Trying to use real API without configuring API key

**Solution**: Either:
1. Set `USE_MOCKS=true` to use mock data
2. Set `ALPHA_VANTAGE_API_KEY=your_key` environment variable

### Mock data not being used

**Problem**: Still making real API calls despite `USE_MOCKS=true`

**Solution**: Check that:
1. Environment variable is set correctly (case-sensitive)
2. No explicit `use_mock=False` in source initialization
3. Config module is being imported correctly

### Can't find environment variables

**Problem**: Environment variables not being loaded

**Solution**: 
1. Check that variables are set in your shell session
2. If using `.env` file, ensure it's in the correct location
3. Verify with: `python -c "import os; print(os.getenv('USE_MOCKS'))"`
