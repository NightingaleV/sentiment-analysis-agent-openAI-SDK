# Sentiment Analysis Agent

Agentic sentiment analysis for stock market news. This project provides tools to fetch news from multiple sources, score content for sentiment/relevance/impact using ML models, and produce structured reports that can be consumed by downstream agents.

Key points:
- Python 3.12+; Pydantic models for structured inputs/outputs
- Sources: Alpha Vantage (pre-scored), Bing News (raw RSS)
- ML-based scoring pipeline (HuggingFace models) with async support
- Agent orchestration to synthesize deterministic aggregates with LLM-generated narratives

Contents
- Features
- Installation
- Quickstart
- Examples
- Development
- Documentation
- Contributing
- License

## Features
- Multi-source news aggregation (Alpha Vantage, Bing News)
- Deterministic aggregation and heuristic scoring (relevance, impact)
- Pluggable scoring pipeline using HuggingFace / PyTorch models
- Strict Pydantic data models for reliability and testability
- Tests and examples included

## Installation
Requirements: Python 3.12

Install dependencies (recommended):

```bash
git clone <repo-url>
cd sentiment-analysis-agent
uv sync
uv sync --group dev
```

Optional: install the package in editable mode:

```bash
python -m pip install -e .
```

Configuration (env vars):
- USE_MOCKS (default: true): When true, data sources and LLM calls use local mocks where available.
- USE_LLM_MOCKS (default: true): Use mocked LLM responses for faster/dev runs.
- ALPHA_VANTAGE_API_KEY: Required when using Alpha Vantage without mocks.
- OPENAI_API_KEY: Required for real OpenAI calls (only if USE_LLM_MOCKS=false).

Note: By default the project is configured to prefer mocks (USE_MOCKS=true) so examples/tests run without external API keys or large model downloads.

## Quickstart

1) Score a single content item using the scoring pipeline (async example):

```python
import asyncio
from datetime import datetime, timezone

from sentiment_analysis_agent.models.sentiment_analysis_models import SentimentContent
from sentiment_analysis_agent.pipeline import ScoringConfig, SentimentScoringPipeline

async def main():
    content = SentimentContent(
        ticker="AAPL",
        title="Apple reports record quarterly earnings",
        summary="Revenue exceeded expectations",
        published_at=datetime.now(timezone.utc),
        source="example",
    )

    config = ScoringConfig()
    pipeline = SentimentScoringPipeline(config)
    scored = await pipeline.score(content)
    print(f"Sentiment: {scored.sentiment_score:.2f}, Relevance: {scored.relevance_score:.2f}, Impact: {scored.impact_score:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
```

2) Run the AnalyzeSentiment tool with Alpha Vantage (mock) and Bing News (RSS):

```python
import asyncio
from sentiment_analysis_agent.tools.analyze_sentiment import AnalyzeSentimentTool
from sentiment_analysis_agent.data_services import AlphaVantageNewsSource, BingNewsRSSSource
from sentiment_analysis_agent.pipeline import ScoringConfig, SentimentScoringPipeline

async def main():
    pipeline = SentimentScoringPipeline(ScoringConfig())

    sources = [
        AlphaVantageNewsSource(use_mock=True),
        BingNewsRSSSource(),
    ]

    tool = AnalyzeSentimentTool(sources=sources, scoring_pipeline=pipeline)
    result = await tool.run(ticker="AAPL", time_window="short", limit=10)

    print("Overall sentiment:", result.overall_sentiment_score)
    print("Breakdown:", result.breakdown)

if __name__ == "__main__":
    asyncio.run(main())
```

3) Convenience: use the SentimentAnalysisAgent to generate a full SentimentReport (narrative requires LLM behavior unless mocks are enabled):

```python
import asyncio
from sentiment_analysis_agent.agents.sentiment_agent import SentimentAnalysisAgent

# build AnalyzeSentimentTool as above (tool)
# agent = SentimentAnalysisAgent(analyze_tool=tool)
# report = asyncio.run(agent.run_for_ticker("AAPL", time_window="short"))
# print(report.summary)
```

## Examples
- `examples/test_pipeline_example.py` — end-to-end integration example. Warning: running it with real models may download large model weights and be slow. Use `USE_MOCKS=true` for quick runs.
- `examples/test_sources.py` — simple example for data sources.

## Development
- Run tests: `uv run pytest`
- Run a single test file: `uv run pytest tests/test_bing_news.py`
- Run with coverage: `uv run pytest --cov=sentiment_analysis_agent`
- Format: `uv run black --line-length 120 .`
- Lint: `uv run pylint sentiment_analysis_agent`
- Preview docs: `uv run mkdocs serve` or `mkdocs serve`

Project coding & testing guidelines are in `AGENTS.md` and `tests/AGENTS.md`.

## Project structure (top-level)

```
sentiment-analysis-agent/
├── sentiment_analysis_agent/    # package code (pipeline, agents, data_services, models)
├── tests/                        # unit & integration tests
├── docs/                         # documentation site (mkdocs)
├── examples/                     # runnable examples
├── pyproject.toml                # project configuration & dependencies
├── SPECS.md                      # project specification and goals
└── AGENTS.md                     # developer guidelines and conventions
```

## Documentation
See `docs/index.md` for a getting started guide and API reference. See `SPECS.md` for design decisions and high-level requirements.

## Contributing
Contributions are welcome. Follow the repository guidelines in `AGENTS.md`:
- Python 3.12+, strict type hints
- Pydantic models for validation
- Google-style docstrings (used by mkdocstrings)
- Tests for new features and documented error paths
- Use conventional commits (e.g., `feat:`, `fix:`, `test:`, `docs:`)

If you plan to run or extend LLM behavior, check `config.py` for `USE_LLM_MOCKS` and `OPENAI_API_KEY` settings.

## License
No license file included in this repository. If you intend to make this project public under an open-source license, add a LICENSE file.

## Acknowledgements
Built with: OpenAI, HuggingFace transformers, PyTorch, Pydantic, httpx.

---

If you'd like, I can open a branch and create a PR that replaces the current README with this version. Would you like me to do that?