
# Sentiment Analysis Agent Specification

## Background / Definition
We want to build an AI agent (OpenAI SDK / Agents SDK) that analyzes sentiment of stock market news articles and provides
insights. The agent should be able to fetch news articles from various sources, analyze sentiment using NLP techniques,
and generate a report summarizing the overall sentiment towards specific stocks or the market as a whole.

The output report will serve as input for another AI agent that makes stock trading decisions. The report should include:
- Key metrics such as positive/negative/neutral sentiment percentages
- Reasoning behind the sentiment classification
- Recommendations for next actions / what to monitor

## Goal
Produce a structured, machine-readable sentiment report for a stock ticker over a defined time window using news content
from multiple sources. The report is intended to be consumed by another agent that makes trading decisions.

## Non-goals
- Execute trades or place orders.
- Provide investment advice to end users (this is a pipeline component, not a consumer product).

## Technology
- Python 3.12+
- Pydantic 2.x models for structured input/output
- HTTP clients for data sources (e.g. `httpx`)
- LLM integration (planned): OpenAI Agents SDK (tool calling + structured outputs)

## Core Data Models
All sources, tools, and agents must use the Pydantic models in `sentiment_analysis_agent/models/sentiment_analysis_models.py`.

Key types:
- `SentimentContent`: raw content item (headline/article/post)
- `SentimentContentScore`: a scored content item (polarity/relevance/impact + reasoning)
- `SentimentReport`: aggregated sentiment report for a ticker/time window

## Architecture Overview
The system is intentionally split into two phases:
1. **Fetch/normalize/score content** → `list[SentimentContentScore]`
2. **Aggregate overall sentiment metrics** → deterministic aggregates used by the agent to build `SentimentReport`

This keeps the agent simple and makes the pipeline reusable:
- If a source already provides sentiment scores (Alpha Vantage), we can skip LLM scoring.
- If a source provides only headlines/articles (RSS/Bing feed), we score the content using a scoring service.

### Components
The AI agent is structured into several key components:
1. Data Source Collection Service: fetches articles from APIs, RSS feeds, and/or scraping.
2. Agent Toolset: tools to fetch content and compute aggregate metrics.
3. Sentiment Analysis Agent: orchestrates tools and produces `SentimentReport`.
4. Data Models: Pydantic schemas used across services/agents.

## Agent Tools (Capabilities)
Tools are Python functions/classes the agent can call. They may be exposed as LLM tools, but they should also work as
regular Python methods so we can test them deterministically.

### Tool 1: Analyze Sentiment (Master Tool)
**Purpose**: Orchestrate fetching, scoring, and aggregating sentiment data into a rich context object.

**Input**:
- `ticker`: Stock symbol.
- `time_window`: Categorical horizon ("short", "medium", "long").
- `limit`: Max items to return (default 50).

**Output**:
- `SentimentAnalysisInput`: A fully populated data model containing:
    - List of `SentimentContentScore` (raw content + scores).
    - Pre-computed `SentimentBreakdown` (counts/ratios).
    - `overall_sentiment_score`, `overall_relevance_score`, `overall_impact_score`.
    - `top_drivers` (highest weighted content).

**Responsibilities**:
- Call all configured data sources (Alpha Vantage, Bing, etc.).
- Score raw content using the internal scoring pipeline.
- Deduplicate items.
- Aggregate metrics deterministically (weighted averages, breakdowns).
- Return the "ready-to-use" context for the Agent to summarize.

### Internal Components (Not LLM-exposed)
These are helper classes used by the master tool:
- `SentimentAggregator`: Static logic for computing breakdown and weighted scores.
- `SentimentScoringPipeline`: ML-based scorer for raw text.



## Data Sources
Each data source should be implemented as a separate class that adheres to a common interface. This allows us to add or
remove sources without changing the agent orchestration.

### Required interface (conceptual)
- `fetch(ticker, start_time, end_time, limit) -> list[SentimentContent] | list[SentimentContentScore]`
- `source_name: str`
- `returns_scored: bool` (or separate subclasses for raw vs scored sources)

### Alpha Vantage News Sentiment (pre-scored)
- Mock response is available in `sentiment_analysis_agent/resources/mocks/alpha_vantage_mock.py`.
- When `limit` is set: return top N articles with the highest relevance score to the given ticker.
- Map Alpha Vantage items to:
  - `SentimentContent` (title/summary/url/published_at/source metadata)
  - `SentimentContentScore` (sentiment/relevance + optional reasoning/confidence/model_name)

### Bing News Search RSS feed (raw-only)
We will also analyze news from Bing News Search:
`https://www.bing.com/news/search?q=AAPL&qft=interval%3d%228%22&form=PTFTNR`

- Fetch headlines/articles for the ticker/time window and map to `SentimentContent`.
- These items must be scored by the scoring pipeline before aggregation/report generation.
- Note: Bing can be tricky (infinite scroll / HTML changes). Prefer RSS if available; otherwise implement robust scraping.

## Potential Development Ideas for News Sources (Future)
We could also analyze articles from these websites:

RSS feeds:
- https://www.reuters.com/tools/rss
- https://seekingalpha.com/market_currents.xml
- https://www.marketwatch.com/rss/topstories

Headlines-only (easy to scrape):
- https://seekingalpha.com/api/sa/combined/AAPL.xml
- https://www.nasdaq.com/feed/rssoutbound?symbol=AAPL
- https://news.google.com/rss/search?q=AAPL&hl=en-US&gl=US&ceid=US:en

## Sentiment Scoring Pipeline (Raw → Scored)
For sources that provide only raw content:
- Input: a single `SentimentContent`
- Output: `SentimentContentScore`

Scoring fields:
- `sentiment_score`: -1..1 (bearish..bullish)
- `relevance_score`: 0..1 (how related is it to the ticker)
- `impact_score`: 0..1 (estimated market impact)
- `reasoning`: short explanation for the scores (used for traceability)

In the pipeline, we will use a finance-tuned model for sentiment scoring. Candidates to evaluate:
- https://huggingface.co/mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis?inference_provider=hf-inference
- https://huggingface.co/msr2903/mrm8488-distilroberta-fine-tuned-financial-sentiment

## Sentiment Analysis Agent
**Primary responsibility**: orchestrate tool calls and return `SentimentReport` (structured output only).

The agent will be integrated with the LangGraph framework with other agents in future. So we will follow the design patterns similar as per LangGraph framework.

### Inputs
The agent should accept either:
- a request containing `ticker + time window` (agent performs fetching/scoring/aggregation)
- `ticker + time window + pre-scored contents` (agent skips fetching/scoring and only aggregates + generates report)

### Execution flow (happy path)
1. Validate inputs and normalize ticker.
2. Call **AnalyzeSentimentTool** (Master Tool).
3. Tool fetches, scores, and aggregates data.
4. Agent receives fully populated `SentimentAnalysisInput`.
5. Agent synthesizes the final `SentimentReport` (Summary, Reasoning, Recommendation).
6. Return `SentimentReport`.

### Error handling
- Source failures should degrade gracefully (partial data is allowed); the report should still be produced when possible.
- Implement retries/backoff for transient HTTP errors and LLM calls.
- Always return timezone-aware UTC timestamps.

## Implementation Plan

1. **Data models & config**: Confirm sentiment_analysis.py matches SPECS fields (SentimentContent, SentimentContentScore, SentimentReport), add any missing enums/time-window helpers, and ensure UTC handling + type-safe inputs.
2. **Data source layer**: Define a base source interface (source_name, returns_scored, fetch signature) and implement Alpha Vantage (using alpha_vantage_mock.py for dev) plus Bing RSS/headlines fetchers with normalization, dedupe by URL/content_id, and time-window filters; wire caching knobs (per ticker/window).
3. **Scoring pipeline**: Build FetchRawContentTool and ScoreContentTool to convert raw SentimentContent → SentimentContentScore with pluggable sentiment model (LLM-backed or mock), apply per-content hash cache, and allow relevance/impact weighting config.
4. **Aggregation tool**: Implement deterministic metric aggregation (counts/percentages, weighted sentiment, relevance/impact aggregates, top drivers ordered by relevance*impact, optional dispersion flags) without LLM usage.
5. **Agent orchestration**: Create the Sentiment Analysis Agent (OpenAI Agents SDK) that validates inputs, fetches+scores content, calls the aggregator, then synthesizes narrative fields into a SentimentReport with graceful degradation/retries and structured outputs only.

## Non-functional Requirements

**Quality gates:** Add pytest coverage for sources (mocked HTTP), scoring pipeline, aggregator math, and agent flow; include fixtures for time windows and mocks. Don't overcomplicate tests, but I want to have basic things covered. 

**Documentation**: Document usage/run instructions and architecture in README. Add google style docstrings to all public methods/classes.

**KISS**: Keep things simple and modular. Avoid over-engineering or premature optimization. Focus on clear, maintainable code.