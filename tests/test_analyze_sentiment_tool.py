"""Tests for AnalyzeSentimentTool."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from sentiment_analysis_agent.models.sentiment_analysis_models import (
    SentimentContent,
    SentimentContentScore,
)
from sentiment_analysis_agent.tools.analyze_sentiment import AnalyzeSentimentTool


@pytest.fixture
def mock_source_scored():
    """Mock source returning scored content."""
    source = MagicMock()
    source.source_name = "mock_scored"
    source.returns_scored = True

    # Mock return value
    item = SentimentContentScore(
        content=SentimentContent(ticker="AAPL", title="Scored 1", url="u1"),
        sentiment_score=0.9,
        relevance_score=0.9,
        impact_score=0.9,
    )
    source.fetch = AsyncMock(return_value=[item])
    return source


@pytest.fixture
def mock_source_raw():
    """Mock source returning raw content."""
    source = MagicMock()
    source.source_name = "mock_raw"
    source.returns_scored = False

    # Mock return value
    item = SentimentContent(ticker="AAPL", title="Raw 1", url="u2")
    source.fetch = AsyncMock(return_value=[item])
    return source


@pytest.fixture
def mock_pipeline():
    """Mock scoring pipeline."""
    pipeline = MagicMock()

    # Mock score_batch behavior
    async def score_batch(contents):
        results = []
        for c in contents:
            results.append(
                SentimentContentScore(
                    content=c,
                    sentiment_score=-0.5,
                    relevance_score=0.5,
                    impact_score=0.5,
                )
            )
        return results

    pipeline.score_batch = AsyncMock(side_effect=score_batch)
    return pipeline


@pytest.mark.asyncio
async def test_run_happy_path(mock_source_scored, mock_source_raw, mock_pipeline):
    """Test full execution flow with mixed sources."""
    tool = AnalyzeSentimentTool(
        sources=[mock_source_scored, mock_source_raw],
        scoring_pipeline=mock_pipeline,
    )

    result = await tool.run(ticker="AAPL", time_window="short", limit=10)

    # Check Inputs
    assert result.ticker == "AAPL"
    assert result.limit == 10

    # Check Contents (1 from scored, 1 from raw)
    assert len(result.contents) == 2

    # Verify titles to ensure both sources contributed
    titles = sorted([c.content.title for c in result.contents])
    assert titles == ["Raw 1", "Scored 1"]

    # Check Aggregates (Scored=0.9, Raw=-0.5 -> Avg ~0.2)
    # Weight Scored: 0.9 * 0.9 = 0.81
    # Weight Raw: 0.5 * 0.5 = 0.25
    # Weighted Sum: (0.9 * 0.81) + (-0.5 * 0.25) = 0.729 - 0.125 = 0.604
    # Total Weight: 0.81 + 0.25 = 1.06
    # Weighted Avg: 0.604 / 1.06 = 0.569...
    assert 0.56 <= result.overall_sentiment_score <= 0.58

    # Verify breakdown exists
    assert result.breakdown is not None
    assert result.breakdown.positive == 1
    assert result.breakdown.negative == 1


@pytest.mark.asyncio
async def test_run_empty_results(mock_pipeline):
    """Test flow when sources return nothing."""
    empty_source = MagicMock()
    empty_source.fetch = AsyncMock(return_value=[])
    empty_source.returns_scored = False

    tool = AnalyzeSentimentTool(
        sources=[empty_source],
        scoring_pipeline=mock_pipeline,
    )

    result = await tool.run(ticker="AAPL")

    assert len(result.contents) == 0
    assert result.overall_sentiment_score == 0.0
    assert result.breakdown.positive == 0
