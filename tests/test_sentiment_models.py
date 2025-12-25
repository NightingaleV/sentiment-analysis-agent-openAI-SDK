from datetime import datetime, timezone
import math

import pytest
from pydantic import ValidationError

from sentiment_analysis_agent.models.sentiment_analysis_models import (
    MarketTrend,
    SentimentAnalysisInput,
    SentimentBreakdown,
    SentimentContent,
    SentimentContentScore,
    SentimentReport,
    Signal,
    TimeWindow,
)


def test_time_window_to_time_range_returns_expected_bounds():
    end_time = datetime(2024, 1, 10, 15, 30)

    start, end = TimeWindow.SHORT_TERM.to_time_range(end_time)

    assert start == datetime(2024, 1, 3, 15, 30, tzinfo=timezone.utc)
    assert end == datetime(2024, 1, 10, 15, 30, tzinfo=timezone.utc)


def test_sentiment_analysis_input_time_window_populates_missing_bounds():
    end_time = datetime(2024, 2, 10, 12, 0)

    params = SentimentAnalysisInput(ticker=" msft ", time_window="medium term", end_time=end_time)

    assert params.ticker == "MSFT"
    assert params.time_window is TimeWindow.MEDIUM_TERM
    assert params.start_time == datetime(2024, 1, 11, 12, 0, tzinfo=timezone.utc)
    assert params.end_time == datetime(2024, 2, 10, 12, 0, tzinfo=timezone.utc)


def test_sentiment_analysis_input_requires_time_information():
    with pytest.raises(ValidationError):
        SentimentAnalysisInput(ticker="AAPL")


def test_sentiment_breakdown_auto_calculates_ratios():
    breakdown = SentimentBreakdown(positive=2, negative=1, neutral=1)

    assert math.isclose(breakdown.positive_ratio, 0.5)
    assert math.isclose(breakdown.negative_ratio, 0.25)
    assert math.isclose(breakdown.neutral_ratio, 0.25)


def test_sentiment_breakdown_zero_total_allows_zero_ratios():
    breakdown = SentimentBreakdown(positive=0, negative=0, neutral=0)

    assert breakdown.positive_ratio == 0.0
    assert breakdown.negative_ratio == 0.0
    assert breakdown.neutral_ratio == 0.0


def test_sentiment_breakdown_rejects_invalid_ratio_sum():
    with pytest.raises(ValidationError):
        SentimentBreakdown(
            positive=1,
            negative=0,
            neutral=0,
            positive_ratio=0.6,
            negative_ratio=0.3,
            neutral_ratio=0.0,
        )


def test_sentiment_report_normalizes_fields_to_utc_and_uppercase():
    content = SentimentContent(content_id="1", ticker="aapl", title="Headline")
    score = SentimentContentScore(
        content=content,
        sentiment_score=0.2,
        impact_score=0.7,
        relevance_score=0.8,
        scored_at=datetime(2024, 1, 5, 12, 0),
    )
    breakdown = SentimentBreakdown(positive=1, negative=0, neutral=0)

    report = SentimentReport(
        ticker="aapl",
        time_window=TimeWindow.SHORT_TERM,
        time_period=(datetime(2024, 1, 1, 0, 0), datetime(2024, 1, 10, 0, 0)),
        generated_at=datetime(2024, 1, 11, 0, 0),
        market_trend=MarketTrend.BULLISH,
        signal=Signal.BUY,
        summary="Summary",
        reasoning="Reasoning",
        sentiment_score=0.2,
        relevance_score=0.8,
        impact_score=0.7,
        breakdown=breakdown,
        contents=[score],
        top_drivers=[score],
    )

    start, end = report.time_period
    assert report.ticker == "AAPL"
    assert start.tzinfo is timezone.utc
    assert end.tzinfo is timezone.utc
    assert report.generated_at.tzinfo is timezone.utc
    assert report.top_drivers[0].content.ticker == "AAPL"
