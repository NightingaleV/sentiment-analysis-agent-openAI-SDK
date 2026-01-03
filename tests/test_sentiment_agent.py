"""Tests for the SentimentAnalysisAgent orchestration layer."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from sentiment_analysis_agent.agents.sentiment_agent import SentimentAnalysisAgent
from sentiment_analysis_agent.models.agent_models import SentimentReportNarrative
from sentiment_analysis_agent.models.sentiment_analysis_models import (
    MarketTrend,
    SentimentAnalysisInput,
    SentimentContent,
    SentimentContentScored,
    Signal,
    TimeWindow,
)
from sentiment_analysis_agent.pipeline.sentiment_aggregator import SentimentAggregator


class StubNarrativeGenerator:
    """Simple stub that returns fixed narrative data and records calls."""

    def __init__(self):
        self.calls: list[tuple[SentimentAnalysisInput, MarketTrend, Signal]] = []

    async def generate(self, context, market_trend, signal):
        self.calls.append((context, market_trend, signal))
        return SentimentReportNarrative(
            summary="stub summary",
            reasoning="stub reasoning",
            highlights=[driver.content.title for driver in context.top_drivers or []],
            recommendations=[f"monitor {context.ticker}"],
        )


def _make_scored(
    title: str, sentiment: float, relevance: float, impact: float
) -> SentimentContentScored:
    content = SentimentContent(
        ticker="AAPL",
        title=title,
        url=f"https://example.com/{title}",
        published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    return SentimentContentScored(
        content=content,
        sentiment_score=sentiment,
        relevance_score=relevance,
        impact_score=impact,
    )


@pytest.mark.asyncio
async def test_pre_scored_request_skips_tool_and_aggregates():
    narrative = StubNarrativeGenerator()
    analyze_tool = AsyncMock()
    contents = [
        _make_scored("Bullish", 0.7, 0.9, 0.8),
        _make_scored("Slight dip", -0.2, 0.4, 0.3),
    ]

    request = SentimentAnalysisInput(
        ticker="AAPL",
        time_window=TimeWindow.SHORT_TERM,
        limit=2,
        contents=contents,
    )
    agent = SentimentAnalysisAgent(
        analyze_tool=analyze_tool, narrative_generator=narrative
    )

    report = await agent.run(request)

    analyze_tool.run.assert_not_called()
    assert report.sentiment_score == pytest.approx(0.57, rel=1e-2)
    assert report.top_drivers[0].content.title == "Bullish"
    assert narrative.calls and narrative.calls[0][1] == MarketTrend.BULLISH


@pytest.mark.asyncio
async def test_agent_fetches_when_contents_absent():
    narrative = StubNarrativeGenerator()
    analyze_tool = AsyncMock()
    fetched_contents = [_make_scored("Fetched", 0.3, 0.8, 0.6)]
    aggregates = SentimentAggregator.aggregate(fetched_contents)
    analyze_tool.run.return_value = SentimentAnalysisInput(
        ticker="AAPL",
        time_window=TimeWindow.SHORT_TERM,
        limit=5,
        contents=fetched_contents,
        start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 8, tzinfo=timezone.utc),
        **aggregates,
    )

    request = SentimentAnalysisInput(
        ticker="AAPL", time_window=TimeWindow.SHORT_TERM, contents=[]
    )
    agent = SentimentAnalysisAgent(
        analyze_tool=analyze_tool, narrative_generator=narrative
    )

    report = await agent.run(request)

    analyze_tool.run.assert_awaited_once()
    assert report.contents[0].content.title == "Fetched"
    assert report.signal in {Signal.BUY, Signal.STRONG_BUY}


@pytest.mark.asyncio
async def test_agent_handles_no_content_gracefully():
    narrative = StubNarrativeGenerator()
    analyze_tool = AsyncMock()
    empty_aggregates = SentimentAggregator.aggregate([])
    analyze_tool.run.return_value = SentimentAnalysisInput(
        ticker="AAPL",
        time_window=TimeWindow.SHORT_TERM,
        limit=10,
        contents=[],
        start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 8, tzinfo=timezone.utc),
        **empty_aggregates,
    )

    request = SentimentAnalysisInput(
        ticker="AAPL", time_window=TimeWindow.SHORT_TERM, contents=[]
    )
    agent = SentimentAnalysisAgent(
        analyze_tool=analyze_tool, narrative_generator=narrative
    )

    report = await agent.run(request)

    assert report.market_trend == MarketTrend.NEUTRAL
    assert report.signal == Signal.HOLD
    assert report.contents == []
    assert narrative.calls and narrative.calls[0][0].ticker == "AAPL"
