"""Interfaces and defaults for the sentiment analysis agent layer."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from sentiment_analysis_agent.models.agent_models import SentimentReportNarrative
from sentiment_analysis_agent.models.sentiment_analysis_models import (
    MarketTrend,
    SentimentAnalysisInput,
    Signal,
)


@runtime_checkable
class NarrativeGenerator(Protocol):
    """Contract for generating narrative fields for a sentiment report."""

    async def generate(
        self,
        context: SentimentAnalysisInput,
        market_trend: MarketTrend,
        signal: Signal,
    ) -> SentimentReportNarrative:
        """Produce narrative fields for a given deterministic context."""


class MockNarrativeGenerator:
    """Deterministic narrative generator for tests and offline runs."""

    def __init__(self, summary_template: str | None = None):
        self.summary_template = (
            summary_template or "{ticker} sentiment is {trend} based on {count} items."
        )

    async def generate(
        self,
        context: SentimentAnalysisInput,
        market_trend: MarketTrend,
        signal: Signal,
    ) -> SentimentReportNarrative:
        summary = self.summary_template.format(
            ticker=context.ticker,
            trend=market_trend.value,
            count=len(context.contents),
        )
        reasoning = f"Deterministic narrative using {len(context.contents)} scored items with signal {signal.value}."
        highlights = [c.content.title for c in context.contents[:3] if c.content.title]
        recommendations = [
            f"Monitor {context.ticker} news during the {context.time_window.value if context.time_window else 'given'} window.",
            f"Re-evaluate when new items appear or if impact shifts beyond the current {context.limit} item limit.",
        ]
        return SentimentReportNarrative(
            summary=summary,
            reasoning=reasoning,
            highlights=highlights,
            recommendations=recommendations,
        )
