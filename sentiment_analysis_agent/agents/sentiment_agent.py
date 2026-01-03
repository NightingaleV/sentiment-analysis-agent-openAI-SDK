"""OpenAI Agents SDK powered sentiment analysis agent."""

from __future__ import annotations

from typing import Iterable

from sentiment_analysis_agent.agents.base import (
    MockNarrativeGenerator,
    NarrativeGenerator,
)
from sentiment_analysis_agent.agents.openai_adapter import OpenAINarrativeGenerator
from sentiment_analysis_agent.models.agent_models import SentimentReportNarrative
from sentiment_analysis_agent.models.sentiment_analysis_models import (
    MarketTrend,
    SentimentAnalysisInput,
    SentimentReport,
    Signal,
    TimeWindow,
    _utcnow,
)
from sentiment_analysis_agent.pipeline.sentiment_aggregator import SentimentAggregator
from sentiment_analysis_agent.tools.analyze_sentiment import AnalyzeSentimentTool


class SentimentAnalysisAgent:
    """Coalesce deterministic metrics with LLM narratives to produce `SentimentReport`."""

    def __init__(
        self,
        analyze_tool: AnalyzeSentimentTool,
        narrative_generator: NarrativeGenerator | None = None,
    ):
        self.analyze_tool = analyze_tool
        self.narrative_generator: NarrativeGenerator = (
            narrative_generator or OpenAINarrativeGenerator()
        )

    async def run(self, request: SentimentAnalysisInput) -> SentimentReport:
        """Generate a sentiment report from pre-scored or fetched content."""

        context = await self._prepare_context(request)
        context = self._ensure_aggregates(context)

        sentiment_score = context.overall_sentiment_score or 0.0
        relevance_score = context.overall_relevance_score or 0.0
        impact_score = context.overall_impact_score or 0.0
        breakdown = context.breakdown or SentimentAggregator.aggregate([])["breakdown"]
        contents = context.contents or []
        top_drivers = context.top_drivers or []
        start_time = context.start_time or _utcnow()
        end_time = context.end_time or start_time

        market_trend = self._derive_market_trend(sentiment_score)
        signal = self._derive_signal(sentiment_score, impact_score)

        narrative: SentimentReportNarrative = await self.narrative_generator.generate(
            context=context,
            market_trend=market_trend,
            signal=signal,
        )

        return SentimentReport(
            ticker=context.ticker,
            time_window=context.time_window,
            time_period=(start_time, end_time),
            generated_at=_utcnow(),
            market_trend=market_trend,
            signal=signal,
            summary=narrative.summary,
            reasoning=narrative.reasoning,
            highlights=narrative.highlights,
            recommendations=narrative.recommendations,
            sentiment_score=sentiment_score,
            relevance_score=relevance_score,
            impact_score=impact_score,
            breakdown=breakdown,
            contents=contents,
            top_drivers=top_drivers,
        )

    async def run_for_ticker(
        self, ticker: str, time_window: str = "short", limit: int = 50
    ) -> SentimentReport:
        """Convenience wrapper when the caller has no pre-scored contents."""

        window = self._coerce_time_window(time_window)
        context = await self.analyze_tool.run(
            ticker=ticker, time_window=window.value, limit=limit
        )
        return await self.run(context)

    async def _prepare_context(
        self, request: SentimentAnalysisInput
    ) -> SentimentAnalysisInput:
        if not request.contents:
            window = request.time_window or TimeWindow.SHORT_TERM
            return await self.analyze_tool.run(
                ticker=request.ticker,
                time_window=window.value,
                limit=request.limit,
            )

        filtered = self._filter_contents(request.contents, request.ticker)
        limited = list(filtered)[: request.limit]
        aggregates = SentimentAggregator.aggregate(limited)
        return request.model_copy(update={"contents": limited, **aggregates})

    def _filter_contents(self, contents: Iterable, ticker: str) -> list:
        """Ensure contents align with the request ticker."""

        matched = [item for item in contents if item.content.ticker == ticker]
        return matched or list(contents)

    def _ensure_aggregates(
        self, context: SentimentAnalysisInput
    ) -> SentimentAnalysisInput:
        contents = context.contents[: context.limit]
        aggregates = SentimentAggregator.aggregate(contents)
        return context.model_copy(update={"contents": contents, **aggregates})

    def _derive_market_trend(self, sentiment_score: float) -> MarketTrend:
        if sentiment_score >= 0.6:
            return MarketTrend.GREEDY
        if sentiment_score >= 0.2:
            return MarketTrend.BULLISH
        if sentiment_score > -0.2:
            return MarketTrend.NEUTRAL
        if sentiment_score > -0.6:
            return MarketTrend.BEARISH
        return MarketTrend.FEARFUL

    def _derive_signal(self, sentiment_score: float, impact_score: float) -> Signal:
        strong_extreme = abs(sentiment_score) >= 0.6 and impact_score >= 0.6
        if strong_extreme:
            if sentiment_score > 0:
                return Signal.STRONG_BUY
            if sentiment_score < 0:
                return Signal.STRONG_SELL
            return Signal.HOLD

        trend = self._derive_market_trend(sentiment_score)
        if trend in (MarketTrend.GREEDY, MarketTrend.BULLISH):
            return Signal.BUY
        if trend in (MarketTrend.BEARISH, MarketTrend.FEARFUL):
            return Signal.SELL
        return Signal.HOLD

    def _coerce_time_window(self, time_window: str) -> TimeWindow:
        try:
            return TimeWindow(time_window)
        except ValueError:
            return TimeWindow.SHORT_TERM
