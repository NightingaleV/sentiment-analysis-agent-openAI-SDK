---
title: OpenAI Agents SDK Sentiment Agent
description: Specification for implementing the sentiment analysis agent using the OpenAI Agents SDK.
icon: material/robot
summary: Add a tool-calling agent that produces `SentimentReport` from `SentimentAnalysisInput` via `AnalyzeSentimentTool`.
---

# OpenAI Agents SDK Sentiment Agent

## Context
What exists today:

- Pydantic schemas are defined in `sentiment_analysis_agent/models/sentiment_analysis_models.py`.
- Data sources are implemented in `sentiment_analysis_agent/data_services/` and conform to `BaseSentimentSource`.
- End-to-end orchestration exists as `AnalyzeSentimentTool` in `sentiment_analysis_agent/tools/analyze_sentiment.py` and returns
  `SentimentAnalysisInput` populated with scored contents and deterministic aggregates.
- The agent package exists (`sentiment_analysis_agent/agents/`) but is currently empty (`base.py` and `sentiment_agent.py` are
  placeholders).
- The project specification includes the intended agent flow in `SPECS.md`.

## Problem
What’s missing/broken and why it matters:

- There is no AI agent implementation that uses the OpenAI Agents SDK to turn `SentimentAnalysisInput` into a structured
  `SentimentReport`.
- Without this agent layer, downstream agents (e.g., trading decision agent) cannot consume a consistent, machine-readable
  sentiment report with narrative fields (summary/reasoning/recommendations).
- The repository currently has no OpenAI configuration surface (env vars, model selection) and no test strategy for the agent flow.

## Goals
- Implement a Sentiment Analysis agent using the OpenAI Agents SDK that:
  - Accepts a request containing either:
    - `ticker + time_window (+ limit)` and performs fetch/score/aggregate via `AnalyzeSentimentTool`, or
    - Pre-scored `contents` and generates a report without re-fetching/re-scoring.
  - Returns a valid `SentimentReport` (Pydantic) with deterministic metrics and LLM-generated narrative fields.
  - Is testable without network access by stubbing the LLM provider.
- Add minimal configuration required to run the agent locally and in CI.

## Non-goals
- Adding new data sources beyond what already exists in `sentiment_analysis_agent/data_services/`.
- Changing the sentiment scoring pipeline implementation (HuggingFace-based) beyond wiring it into the agent.
- Building a CLI, web service, or LangGraph integration in this iteration (keep the agent callable as a Python API).
- Implementing trading decisions or portfolio logic.

## Proposed solution

### High-level design
- Create a single public entrypoint class `SentimentAnalysisAgent` under `sentiment_analysis_agent/agents/sentiment_agent.py` with an
  async method `run(...) -> SentimentReport`.
- Use a two-stage approach to keep outputs reliable:
  1. Deterministic stage (Python): obtain/validate `SentimentAnalysisInput` and compute all numeric fields and derived classifications
     (trend/signal) deterministically.
  2. LLM stage (OpenAI Agents SDK): generate only the narrative fields (summary/reasoning/highlights/recommendations) from the
     deterministic context.
- Assemble the final `SentimentReport` by combining deterministic fields with LLM narrative fields (never letting the LLM “invent”
  metrics).

### Interfaces / API changes
- New Python API:
  - `sentiment_analysis_agent.agents.sentiment_agent.SentimentAnalysisAgent`
    - `__init__(..., analyze_tool: AnalyzeSentimentTool, llm_client: ...)`
    - `run(request: SentimentAnalysisInput) -> SentimentReport` (preferred)
    - Optional convenience overload: `run_for_ticker(ticker: str, time_window: str = "short", limit: int = 50) -> SentimentReport`
- New internal Pydantic model (agent-only) for structured narrative output:
  - `SentimentReportNarrative` with fields:
    - `summary: str`
    - `reasoning: str`
    - `highlights: list[str]`
    - `recommendations: list[str]`
- New environment configuration:
  - `OPENAI_API_KEY` (required when LLM is enabled)
  - `OPENAI_MODEL` (default e.g. `gpt-4.1-mini` or project-chosen model)
  - `USE_LLM_MOCKS` (default `true` in tests/CI to avoid network)

### Data model / storage changes
- No changes to the existing “core” output model `SentimentReport`.
- Add `SentimentReportNarrative` either:
  - in `sentiment_analysis_agent/models/sentiment_analysis_models.py` (preferred for shared visibility), or
  - in a new module `sentiment_analysis_agent/models/agent_models.py` if we want to keep agent-only schemas separate.
- No persistence layer is introduced.

### Agent behavior details

#### Input handling
- The agent accepts `SentimentAnalysisInput` and follows this logic:
  - If `request.contents` is empty:
    - Call `AnalyzeSentimentTool.run(ticker=request.ticker, time_window=request.time_window.value, limit=request.limit)` to obtain a
      fully populated `SentimentAnalysisInput`.
  - If `request.contents` is provided:
    - Validate the contents belong to the target ticker (best-effort: normalize tickers and filter mismatches).
    - Compute aggregates via `SentimentAggregator.aggregate(request.contents)` and construct a “complete” `SentimentAnalysisInput`
      instance for reporting.

#### Deterministic report fields
- `SentimentReport.sentiment_score`, `relevance_score`, `impact_score`, `breakdown`, `top_drivers`, `contents` are sourced from the
  deterministic aggregation results only.
- `market_trend` and `signal` are derived deterministically from `sentiment_score` (and optionally `impact_score`) using project-owned
  thresholds. Example threshold mapping (tunable via config):
  - `market_trend`:
    - `sentiment_score >= 0.6` → `GREEDY`
    - `0.2 <= sentiment_score < 0.6` → `BULLISH`
    - `-0.2 < sentiment_score < 0.2` → `NEUTRAL`
    - `-0.6 < sentiment_score <= -0.2` → `BEARISH`
    - `sentiment_score <= -0.6` → `FEARFUL`
  - `signal`:
    - Strong signals require both extreme sentiment and meaningful impact (e.g., `abs(sentiment_score) >= 0.6 and impact_score >= 0.6`)
    - Otherwise map to `BUY/HOLD/SELL` based on the same sentiment buckets.

#### LLM narrative generation (OpenAI Agents SDK)
- Use the OpenAI Agents SDK with a single “narrative generator” agent that:
  - Receives the deterministic context (ticker, window, period, numeric metrics, and a compact list of top drivers with titles, dates,
    and scores).
  - Outputs `SentimentReportNarrative` as a structured response.
- Narrative constraints:
  - No numbers unless directly copied from provided metrics.
  - Use concise language; avoid investment advice phrasing; focus on “monitoring signals”.
  - `highlights` and `recommendations` are short strings suitable for another agent to parse.

### Edge cases
- No content available:
  - Return a `SentimentReport` with zeros, `NEUTRAL` trend, `HOLD` signal, and narrative indicating insufficient data.
- Partial source failures:
  - `AnalyzeSentimentTool` already degrades gracefully; the agent should still produce a report from partial data.
- Invalid `time_window` string:
  - Normalize via `TimeWindow(value)` with fallback to `TimeWindow.SHORT_TERM` (consistent with `AnalyzeSentimentTool` behavior).
- Ticker normalization:
  - Always uppercase and strip whitespace (Pydantic validators already enforce this on models).

## Acceptance criteria
- [ ] A new spec-aligned `SentimentAnalysisAgent` exists in `sentiment_analysis_agent/agents/sentiment_agent.py` and can be imported.
- [ ] Agent can generate a `SentimentReport` given `SentimentAnalysisInput` with empty `contents` (uses `AnalyzeSentimentTool`).
- [ ] Agent can generate a `SentimentReport` given `SentimentAnalysisInput` with pre-scored `contents` (skips fetching/scoring).
- [ ] Numeric and categorical fields (`sentiment_score`, `relevance_score`, `impact_score`, `breakdown`, `market_trend`, `signal`) are
      deterministic and reproducible for the same inputs.
- [ ] Narrative fields (`summary`, `reasoning`, `highlights`, `recommendations`) are produced via the OpenAI Agents SDK (and can be
      mocked in tests).
- [ ] Unit tests cover the happy path, empty-content path, and pre-scored-content path without requiring network.
- [ ] Configuration documents include OpenAI settings and default behavior for mocks.

## Implementation plan
1) Add OpenAI configuration and dependencies (`OPENAI_API_KEY`, model selection, mock toggle).
2) Implement deterministic report builder (aggregate → trend/signal → base `SentimentReport` fields).
3) Implement OpenAI Agents SDK narrative generator returning `SentimentReportNarrative`.
4) Implement `SentimentAnalysisAgent` orchestration (input handling + merge deterministic + narrative).
5) Add unit tests for agent behavior with mocked LLM and mocked `AnalyzeSentimentTool`.
6) Update docs (`docs/reference/configuration.md`) with OpenAI configuration and examples.

## Testing strategy
- Unit:
  - Mock `AnalyzeSentimentTool.run` to return fixed `SentimentAnalysisInput`.
  - Mock the Agents SDK runner/client to return fixed `SentimentReportNarrative`.
  - Assert deterministic fields match aggregation outputs exactly.
- Integration:
  - Optional (behind `@pytest.mark.integration`): run the agent end-to-end with `USE_MOCKS=true` for sources and real OpenAI calls when
    `OPENAI_API_KEY` is configured.
- E2E (if applicable):
  - Not in scope for this iteration.

## Risks & mitigations
- SDK/API churn (Agents SDK is evolving):
  - Isolate SDK usage behind a small adapter module (e.g., `sentiment_analysis_agent/agents/openai_adapter.py`).
- Flaky narrative outputs:
  - Use structured outputs (`SentimentReportNarrative`) and keep deterministic fields out of LLM control.
- Network-restricted CI:
  - Default `USE_LLM_MOCKS=true` in tests; keep integration tests opt-in via marker.

## Rollback / migration plan
- Rollback is a code-only revert:
  - Remove the agent module and OpenAI dependencies/config.
  - No data migrations are required.

## Open questions / assumptions
- Which exact OpenAI Agents SDK package/version should be used (`openai-agents` vs bundled in `openai`)? Lets Use openai-agents
- Preferred default model name for narrative generation (and whether we should support a “cheap” model for dev). Lets support cheap model for dev. Mini gpt5 is good
- Should `market_trend`/`signal` thresholds be configurable (env vars) or hard-coded initially? Hard-coded initially
- Should the agent include URLs in narrative highlights, or keep them as separate structured fields only? Keep them separate, the urls are part of SentimentContentScored
