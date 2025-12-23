
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
All sources, tools, and agents must use the Pydantic models in `sentiment_analysis_agent/models/sentiment_analysis.py`.

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

### Tool 1: Fetch Scored Content
**Purpose**: Fetch content for a ticker/time window from configured source.

**Input** (conceptual):
- `ticker`
- `start_time`, `end_time` (UTC)
- `limit` (max items returned)
- `min_relevance_score` (optional filter)
- `sources` (optional allowlist)

**Output** (conceptual):
- `scored_contents: list[SentimentContentScore]` 

**Responsibilities**:
- Call each configured data source.
- Normalize raw items to `SentimentContent`.
- If the source is pre-scored (Alpha Vantage), map directly to `SentimentContentScore`.
- Keep raw-only items separate (they must be scored by sentiment scoring pipeline before aggregation/reporting).
- De-duplicate items (by URL/content_id) across sources.
- Apply time-window + relevance filtering and enforce `limit`.

**Implementation notes**:
- Prefer deterministic ordering: sort by `(relevance_score * impact_score)` desc, then `published_at` desc.
- Time window will allow only for categorical specification ("short term" = last 7 days, "medium term" = last 30 days, "long term" = last 90 days).
- Cache at two levels:
  - raw fetch cache (per source/ticker/window) - with certain expiration period depending if the fetch is done on short, medium or long term basis
  - score cache (per content hash) to avoid re-scoring duplicates

### Tool 2: Aggregate Overall Sentiment Metrics
**Purpose**: Deterministically aggregate metrics from scored items for report generation.

**Input** (conceptual):
- `ticker`
- `start_time`, `end_time` (UTC)
- `contents: list[SentimentContentScore]`

**Output** (conceptual):
- Counts and percentages: positive / negative / neutral
- Weighted aggregate sentiment score (e.g. weight by `relevance_score * impact_score`)
- Aggregate `relevance_score` and `impact_score` for the time window
- Top drivers: top-N items by `(relevance_score * impact_score)`

**Responsibilities**:
- Compute numeric aggregates (mean/weighted mean, counts, percentages) deterministically.
- Identify top drivers (high impact/relevance items) and notable contradictions/dispersion (optional).
- Provide stable ordering and reproducible results (critical for testing).

**LLM usage guidance**:
- The aggregation tool should not call an LLM.
- Use an LLM only for synthesizing narrative fields / categorical labels inside the agent.

### Optional Internal Tools (Not necessarily LLM-exposed)
These are helpful for testing and keeping responsibilities small:
- `FetchRawContentTool`: returns `list[SentimentContent]` for raw sources (RSS/Bing feed)
- `ScoreContentTool`: converts `list[SentimentContent]` → `list[SentimentContentScore]`


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

### Inputs
The agent should accept either:
- a request containing `ticker + time window` (agent performs fetching/scoring/aggregation)
- `ticker + time window + pre-scored contents` (agent skips fetching/scoring and only aggregates + generates report)

### Execution flow (happy path)
1. Validate inputs and normalize ticker.
2. Call **Fetch Content** tool (raw + pre-scored).
3. Score raw content via scoring service (LLM-backed, mockable).
4. Call **Aggregate Overall Sentiment Metrics** tool.
5. Use aggregates + top drivers to synthesize the final `SentimentReport`.
6. Return `SentimentReport`.

### Error handling
- Source failures should degrade gracefully (partial data is allowed); the report should still be produced when possible.
- Implement retries/backoff for transient HTTP errors and LLM calls.
- Always return timezone-aware UTC timestamps.

## Implementation Checklist
- Define common data source interface and Alpha Vantage + Bing RSS/headlines implementations.
- Implement cache for fetch + scoring steps (rate-limits + de-duplication).
- Implement scoring service for raw content (LLM-backed, mockable).
- Implement deterministic aggregation tool (metrics + top drivers).
- Implement agent report synthesis returning `SentimentReport`.
