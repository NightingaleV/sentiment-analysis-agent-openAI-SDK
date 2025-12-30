"""Tests for the deterministic sentiment aggregator."""

from datetime import datetime, timezone

import pytest
from sentiment_analysis_agent.models.sentiment_analysis_models import (
    SentimentContent,
    SentimentContentScore,
)
from sentiment_analysis_agent.pipeline.sentiment_aggregator import SentimentAggregator


@pytest.fixture
def sample_content_score() -> SentimentContentScore:
    """Create a basic scored content item."""
    return SentimentContentScore(
        content=SentimentContent(
            ticker="AAPL",
            title="Test Article",
            url="http://example.com/1",
        ),
        sentiment_score=0.5,
        relevance_score=0.8,
        impact_score=0.5,
        scored_at=datetime.now(timezone.utc),
    )


def test_aggregate_empty_list():
    """Test aggregation with an empty list of contents."""
    result = SentimentAggregator.aggregate([])

    assert result["overall_sentiment_score"] == 0.0
    assert result["overall_relevance_score"] == 0.0
    assert result["overall_impact_score"] == 0.0
    assert result["top_drivers"] == []

    breakdown = result["breakdown"]
    assert breakdown.positive == 0
    assert breakdown.negative == 0
    assert breakdown.neutral == 0
    assert breakdown.positive_ratio == 0.0


def test_aggregate_single_item(sample_content_score):
    """Test aggregation with a single item."""
    result = SentimentAggregator.aggregate([sample_content_score])

    assert result["overall_sentiment_score"] == 0.5
    assert result["overall_relevance_score"] == 0.8
    assert result["overall_impact_score"] == 0.5
    assert len(result["top_drivers"]) == 1
    assert result["top_drivers"][0] == sample_content_score

    breakdown = result["breakdown"]
    assert breakdown.positive == 1
    assert breakdown.negative == 0
    assert breakdown.neutral == 0
    assert breakdown.positive_ratio == 1.0


def test_aggregate_mixed_sentiment():
    """Test weighted aggregation with mixed sentiment items."""
    # Item 1: High positive, High weight (1.0 * 1.0 = 1.0)
    item1 = SentimentContentScore(
        content=SentimentContent(ticker="A", title="Good", url="u1"),
        sentiment_score=1.0,
        relevance_score=1.0,
        impact_score=1.0,
    )
    # Item 2: Moderate negative, Low weight (0.5 * 0.2 = 0.1)
    item2 = SentimentContentScore(
        content=SentimentContent(ticker="A", title="Bad", url="u2"),
        sentiment_score=-0.5,
        relevance_score=0.5,
        impact_score=0.2,
    )

    result = SentimentAggregator.aggregate([item1, item2])

    # Weights: Item1=1.0, Item2=0.1. Total=1.1
    # Weighted Sum: (1.0 * 1.0) + (-0.5 * 0.1) = 1.0 - 0.05 = 0.95
    # Avg: 0.95 / 1.1 = 0.8636...
    assert result["overall_sentiment_score"] == 0.86

    # Simple averages for relevance/impact
    # Relevance: (1.0 + 0.5) / 2 = 0.75
    # Impact: (1.0 + 0.2) / 2 = 0.6
    assert result["overall_relevance_score"] == 0.75
    assert result["overall_impact_score"] == 0.60

    breakdown = result["breakdown"]
    assert breakdown.positive == 1
    assert breakdown.negative == 1
    assert breakdown.neutral == 0
    assert breakdown.positive_ratio == 0.5
    assert breakdown.negative_ratio == 0.5


def test_aggregate_top_drivers_sorting():
    """Test that top drivers are sorted by weight."""
    # Low weight
    low = SentimentContentScore(
        content=SentimentContent(ticker="A", title="Low", url="u1"),
        sentiment_score=0.1,
        relevance_score=0.1,
        impact_score=0.1,  # weight 0.01
    )
    # High weight
    high = SentimentContentScore(
        content=SentimentContent(ticker="A", title="High", url="u2"),
        sentiment_score=0.9,
        relevance_score=0.9,
        impact_score=0.9,  # weight 0.81
    )
    # Medium weight
    med = SentimentContentScore(
        content=SentimentContent(ticker="A", title="Med", url="u3"),
        sentiment_score=0.5,
        relevance_score=0.5,
        impact_score=0.5,  # weight 0.25
    )

    result = SentimentAggregator.aggregate([low, high, med])
    drivers = result["top_drivers"]

    assert len(drivers) == 3
    assert drivers[0].content.title == "High"
    assert drivers[1].content.title == "Med"
    assert drivers[2].content.title == "Low"


def test_aggregate_zero_weights():
    """Test fallback when all weights are zero."""
    item1 = SentimentContentScore(
        content=SentimentContent(ticker="A", title="1", url="u1"),
        sentiment_score=1.0,
        relevance_score=0.0,
        impact_score=0.0,
    )
    item2 = SentimentContentScore(
        content=SentimentContent(ticker="A", title="2", url="u2"),
        sentiment_score=0.0,
        relevance_score=0.0,
        impact_score=0.0,
    )

    result = SentimentAggregator.aggregate([item1, item2])

    # Should fall back to simple average: (1.0 + 0.0) / 2 = 0.5
    assert result["overall_sentiment_score"] == 0.5
