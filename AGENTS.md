## Persona
Senior Python Developer for Data Analytics & Data Engineering & Machine Learning
As a coding assistant, you have deep expertise in Python, data engineering, machine learning, devops and mlops principles. You write clean, modular, and maintainable code that adheres to software design patterns, best practices, and is free of code smells. You provide context and explain your choices clearly, without repeating yourself, and focus on delivering concise and effective code snippets.  
You follow user's requirements to letter but can suggest more optimal solution.

---

## Project Overview
This is an agentic stock analysis system providing comprehensive reports summarizing various aspects of stocks:

- **Sentiment Analysis** - News and market sentiment analysis

## Sources

- Scraped Capitol Trades data for Insider Trading
- Company financial statements / Market Data - YFinance
- News articles and sentiment data - #TODO: To be Defined

## Implementation Details

## Agents
This project is mainly serve for the learning, so each agent will be implemented with different frameworks in order to get knowledge of the framework.:

- **Sentiment Analysis Agent** - Implemented with OpenAI Agents SDK [Documentation](https://microsoft.github.io/autogen/stable/)


## Tech Stack:
- Python 3.12
- UV to manage dependencies [UV documentation](https://docs.astral.sh/uv/concepts/projects/dependencies/)
- Pyproject.toml for project configuration / dependency management
- Pydantic 2.0 for data validation

## Development Guidelines
- Use conventional commits for commit messages

## High-Level Structure

So as each agent will be implement with different framework, we will separate concerns with separate sub-package for each agent. 

*   Inside project folder we want following structure:
    * `/models`or `models.py`: Data/validation models and schemas.
    * `/prompts`or `prompts.py`: Prompt templates and utilities.
    * `/data_services` or `services.py`: Business logic and service layer.
    * `/agents` or `agents.py`: Agent implementations.
    * `/utils` or `utils.py`: Utility functions and classes.


### Key Design Patterns
The agent will be integrated with the LangGraph framework with other agents in future. So we will follow the design patterns similar as per LangGraph framework.
**Structured Output**: Agents return Pydantic models, not raw text, ensuring consistent data flow
**Data Source Abstraction**: All external data access goes through source classes (`FinanceToolset`, `CapitolTrades`)

## Technology Stack

- **Python 3.12** - Core language (required >=3.12, <3.13)
- **Pydantic 2.0** - Data validation and serialization
- **pandas** - Data manipulation and analysis
- **yfinance** - Financial data retrieval
- **httpx** - Async HTTP client for web scraping

---

# General Workflow

## Agent Requirements & Tips
1. Establish plan of action before you start working
2. Use context7 to update documentation context.

### Using uv (Recommended)

```bash
# Install dependencies
uv sync

# Run in development mode  
uv run python main.py

# Install development dependencies
uv sync --group dev

# Format code
uv run black --line-length 120 agentic_stock_analysis/
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific test file  
uv run pytest test_fundamental_models.py

# Run with coverage
uv run pytest --cov=agentic_stock_analysis
```


## Coding Style & Conventions
- Python 3.12+
- Pythonic idioms and best practices (e.g., PEP 8)
- Use type hints (not in docstrings) for better readability and maintainability.
- Use Pydantic for data validation
- Prefer dataclasses and/or pydantic models for structured data.
- Use class based components.
- Docstrings for every public class/method in Google style.
- Use environment variables for sensitive data
- Use logging for debugging and monitoring

### Type-hints
- Use type hints for function signatures and class attributes.
- Do not use Dict, List, Union, Tuple from typing module, use built-in types instead (e.g. dict, list, tuple).
- Use Pydantic models for complex data structures.


#### Exaple: Type Annotations
```python
# ✅ Good - use built-in types
def process_data(items: list[dict], config: dict[str, str]) -> tuple[int, str]:
    pass

# ❌ Avoid - old typing module imports
from typing import List, Dict, Union, Tuple
def process_data(items: List[Dict], config: Dict[str, str]) -> Tuple[int, str]:
    pass
```

## Documentation
- Use docstrings for all public classes and methods.
- Use Google style docstrings.
- Use clear and concise descriptions.
- If we use python type hints, we dont need to specify types in docstrings.
Instead of:
Args:
  ticker (str): The stock ticker symbol
  period (str, optional): Time period to fetch. Defaults to "1y" (1 year).
  interval (str, optional): Data interval. Defaults to "1d" (daily).
Lets have:
Args:
  ticker: The stock ticker symbol
  period: Time period to fetch. Defaults to "1y" (1 year).
  interval: Data interval. Defaults to "1d" (daily).


## Testing & CI
- Mock external APIs.
- If asked to develop tests, use pytest and mocks.

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

**Format**: `<type>: <description>`

**Types**:
- `feat`: New features
- `fix`: Bug fixes  
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring  
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples**:
- `feat: add trend analysis agent with moving averages`
- `fix: handle empty earnings data in fundamental analysis` 
- `docs: update agent development patterns in WARP.md`
- `refactor: extract common validation logic to base model`

### Environment Configuration

The system uses environment-based configuration with development/production modes:

**Key Environment Variables:**
- `ENVIRONMENT` - "development" or "production" (default: development)
- `OPENAI_API_KEY` - OpenAI API key for GPT models
- `TIINGO_API_KEY` - Tiingo financial data API
- `DEEPSEEK_API_KEY` - DeepSeek LLM API key
- `USE_MOCKS` - Toggle mock data usage (default: True in development)

**Configuration Files:**
- Development: `env/development.env`  
- Production: `env/production.env`

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

**Format**: `<type>: <description>`

**Types**:
- `feat`: New features
- `fix`: Bug fixes  
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring  
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples**:
- `feat: add trend analysis agent with moving averages`
- `fix: handle empty earnings data in fundamental analysis` 
- `docs: update agent development patterns in WARP.md`
- `refactor: extract common validation logic to base model`

## Related Documentation

- [README.md](./README.md) - Project overview and scope
- [AGENTS.md](./AGENTS.md) - Detailed agent development guidelines  

## Adding New Agents

### Step-by-Step Process

1. **Create Agent Class**:
   ```python
   # agentic_stock_analysis/agents/my_new_agent.py
   class MyNewAgent(AsyncAgent):
       SYSTEM_PROMPT = """..."""
       DEFAULT_MODEL = "openai:gpt-4o-mini"
   ```

2. **Create Analysis Model**:
   ```python
   # agentic_stock_analysis/models/my_analysis.py  
   class MyAnalysis(BaseAnalysis):
       # Add specialized fields
       pass
   ```

3. **Add Data Sources** (if needed):
   See [Data Services](#data-services) section below for implementing new data sources.

4. **Update Configuration**:
   - Add any new environment variables to `config/base.py`
   - Add dependencies to `pyproject.toml` if needed

5. **Add Tests**:
   ```python
   # test_my_agent.py
   def test_my_agent():
       # Mock external dependencies
       # Test agent behavior
       pass
   ```

6. **Update Documentation**:
   - Add entry to this AGENTS.md file
   - Update README.md if it affects user-facing features

## Data Services

Data services provide a unified interface for fetching sentiment content from multiple sources.

### Architecture

```
BaseSentimentSource (abstract)
├─ RawSentimentSource → Returns raw content needing sentiment scoring
│   └─ BingNewsRSSSource
│
└─ ScoredSentimentSource → Returns pre-scored content
    └─ AlphaVantageNewsSource
```

### Implemented Sources

**Alpha Vantage News Sentiment** (`data_services/alpha_vantage.py`)
- Type: Pre-scored (returns `list[SentimentContentScore]`)
- Features: High-quality financial news with sentiment/relevance/impact scores
- Configuration: Requires `ALPHA_VANTAGE_API_KEY` or `use_mock=True`

**Bing News RSS Feed** (`data_services/bing_news.py`)
- Type: Raw content (returns `list[SentimentContent]`)
- Features: Recent news headlines, fast and free
- Limitations: Typically returns 10-15 items due to anti-scraping measures

### Usage Example

```python
from sentiment_analysis_agent.data_services import AlphaVantageNewsSource, BingNewsRSSSource

# Fetch pre-scored content
av_source = AlphaVantageNewsSource(use_mock=True)
scored_results = await av_source.fetch_latest("AAPL", horizon="medium", limit=10)

# Fetch raw content (needs scoring)
bing_source = BingNewsRSSSource()
raw_results = await bing_source.fetch_latest("AAPL", horizon="short", limit=5)
```

### Adding New Data Sources

1. **Choose Base Class**:
   - Inherit from `RawSentimentSource` if source returns raw content
   - Inherit from `ScoredSentimentSource` if source provides pre-scored content

2. **Implement Required Methods**:
   ```python
   from sentiment_analysis_agent.data_services.base import RawSentimentSource
   from sentiment_analysis_agent.models.sentiment_analysis_models import SentimentContent
   
   class MyNewsSource(RawSentimentSource):
       @property
       def source_name(self) -> str:
           return "my_news_source"
       
       async def fetch(
           self, ticker: str, start_time: datetime, end_time: datetime, limit: int | None = None
       ) -> list[SentimentContent]:
           # Implement fetching logic
           # Return list of SentimentContent objects
           pass
   ```

3. **Key Requirements**:
   - Use `content_id` auto-generation (hash of ticker, source, URL, published_at)
   - Ensure all timestamps are UTC timezone-aware
   - Normalize ticker to uppercase
   - Handle errors gracefully (network issues, parsing errors)
   - Add mock data support for testing

4. **Export in `__init__.py`**:
   ```python
   # sentiment_analysis_agent/data_services/__init__.py
   from .my_news_source import MyNewsSource
   __all__ = [..., "MyNewsSource"]
   ```

5. **Add Tests**:
   ```python
   # tests/test_my_news_source.py
   @pytest.mark.asyncio
   async def test_my_news_source():
       source = MyNewsSource()
       results = await source.fetch_latest("AAPL", horizon="short", limit=5)
       assert len(results) >= 1
       assert results[0].ticker == "AAPL"
   ```

### Documentation

See detailed documentation:
- [Data Services Guide](docs/guides/data-services.md) - Usage and examples
- [API Reference](docs/api/data-services.md) - Detailed API documentation
- [Configuration Reference](docs/reference/configuration.md) - Configuration options

## Sentiment Scoring Pipeline

The sentiment scoring pipeline transforms raw `SentimentContent` into `SentimentContentScore` using pre-trained financial sentiment models from HuggingFace.

### Overview

The pipeline provides:
1. **Sentiment Classification** - Using finance-tuned DistilRoBERTa models
2. **Relevance Scoring** - Heuristic-based scoring using ticker mentions and content quality
3. **Impact Scoring** - Heuristic-based scoring using content freshness and length
4. **Batch Processing** - Efficient batch inference for multiple content items

### Architecture

```
SentimentScoringPipeline
├─ ScoringConfig (configuration)
├─ ModelFactory (model management)
│   ├─ DistilRobertaFineTunedStrategy (primary model)
│   └─ DistilRobertaBaseStrategy (alternative model)
└─ Heuristic Scoring (relevance + impact)
```

### Models

**Primary Model**: `msr2903/mrm8488-distilroberta-fine-tuned-financial-sentiment`
- Fine-tuned specifically on financial news sentiment
- Achieves 91.71% accuracy on evaluation set
- Returns: positive/negative/neutral with confidence scores

**Alternative Model**: `mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis`
- Base financial sentiment model
- Trained on financial_phrasebank dataset
- Achieves 98.23% accuracy on different dataset

### Usage Examples

#### Basic Usage

```python
import asyncio
from datetime import datetime, timedelta, timezone
from sentiment_analysis_agent.models.sentiment_analysis_models import SentimentContent
from sentiment_analysis_agent.pipeline import SentimentScoringPipeline

async def main():
    # Create pipeline with default configuration
    pipeline = SentimentScoringPipeline()
    
    # Create raw content
    content = SentimentContent(
        ticker="AAPL",
        title="Apple reports record earnings",
        summary="Apple Inc. announced strong quarterly results.",
        published_at=datetime.now(timezone.utc) - timedelta(hours=2),
        source="news_source"
    )
    
    # Score the content
    scored = await pipeline.score(content)
    
    # Access results
    print(f"Sentiment: {scored.sentiment_score}")
    print(f"Relevance: {scored.relevance_score}")
    print(f"Impact: {scored.impact_score}")
    print(f"Reasoning: {scored.reasoning}")

asyncio.run(main())
```

#### Batch Scoring

```python
# Score multiple items efficiently
contents = [content1, content2, content3]
scored_batch = await pipeline.score_batch(contents)

for scored in scored_batch:
    print(f"{scored.content.ticker}: {scored.sentiment_score}")
```

#### Custom Configuration

```python
from sentiment_analysis_agent.pipeline import ScoringConfig, ModelType, Device

# Configure pipeline
config = ScoringConfig(
    model_type=ModelType.DISTILROBERTA_BASE,  # Use alternative model
    device=Device.CPU,  # Force CPU usage
    max_length=256,  # Shorter text limit
    batch_size=16,  # Larger batches
    # Adjust heuristic weights
    relevance_ticker_weight=0.8,
    relevance_length_weight=0.2,
)

pipeline = SentimentScoringPipeline(config)
```

#### Integration with Data Sources

```python
from sentiment_analysis_agent.data_services import BingNewsRSSSource
from sentiment_analysis_agent.pipeline import SentimentScoringPipeline

# Fetch raw content
source = BingNewsRSSSource()
raw_contents = await source.fetch_latest("AAPL", horizon="short", limit=10)

# Score all content
pipeline = SentimentScoringPipeline()
scored_contents = await pipeline.score_batch(raw_contents)

# Filter by relevance
relevant = [s for s in scored_contents if s.relevance_score > 0.5]
```

### Configuration Options

**Model Settings:**
- `model_type`: Which pre-trained model to use (DISTILROBERTA_FINETUNED or DISTILROBERTA_BASE)
- `device`: Computing device (CPU/CUDA/MPS) - auto-detected if None
- `max_length`: Maximum token length (default: 512)
- `batch_size`: Batch size for inference (default: 8)

**Preprocessing:**
- `truncation_strategy`: "smart" (prioritize title/summary) or "head" (simple truncation)

**Heuristic Weights:**
- `relevance_ticker_weight`: Weight for ticker mentions in relevance (default: 0.7)
- `relevance_length_weight`: Weight for content length in relevance (default: 0.3)
- `impact_freshness_weight`: Weight for freshness in impact (default: 0.6)
- `impact_length_weight`: Weight for content length in impact (default: 0.4)

**Score Floors:**
- `min_relevance_score`: Minimum relevance score (default: 0.1)
- `min_impact_score`: Minimum impact score (default: 0.1)

### Scoring Heuristics

**Sentiment Score** (-1 to 1):
- Generated by ML model
- -1.0 = strongly negative
- 0.0 = neutral
- 1.0 = strongly positive

**Relevance Score** (0 to 1):
- Ticker mention frequency (70% weight)
- Content length/quality (30% weight)
- Floor: 0.1 minimum

**Impact Score** (0 to 1):
- Content freshness - exponential decay over time (60% weight)
- Content length/depth (40% weight)
- Floor: 0.1 minimum

### Device Support

The pipeline automatically detects the best available device:
1. **MPS** (Apple Silicon) - For M1/M2/M3 Macs
2. **CUDA** - For NVIDIA GPUs
3. **CPU** - Fallback for any system

You can also explicitly set the device in configuration.

### Testing

```bash
# Run unit tests only (fast)
uv run pytest tests/test_sentiment_pipeline.py -v -m "not integration and not slow"

# Run integration tests with real models (slow)
uv run pytest tests/test_sentiment_pipeline.py -v -m integration

# Run example integration script
uv run python test_pipeline_example.py
```

### Performance Considerations

- **Model Loading**: First inference takes longer (model download + load)
- **Batch Processing**: Use `score_batch()` for multiple items (more efficient)
- **Device Selection**: MPS/CUDA significantly faster than CPU
- **Caching**: Models are cached as singletons (reused across pipeline instances)

## Agents
