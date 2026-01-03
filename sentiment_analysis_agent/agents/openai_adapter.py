"""Adapter around the OpenAI Agents SDK for narrative generation."""

from __future__ import annotations

from typing import Any

from sentiment_analysis_agent.agents.base import NarrativeGenerator
from sentiment_analysis_agent.config import OPENAI_API_KEY, OPENAI_MODEL, USE_LLM_MOCKS
from sentiment_analysis_agent.models.agent_models import SentimentReportNarrative
from sentiment_analysis_agent.models.sentiment_analysis_models import (
    MarketTrend,
    SentimentAnalysisInput,
    Signal,
)


class OpenAINarrativeGenerator(NarrativeGenerator):
    """Generate sentiment report narratives via the OpenAI Agents SDK.

    The generator defaults to a deterministic mock mode (`USE_LLM_MOCKS=true`)
    to keep tests and CI network-free. When mocks are disabled and an API key
    is present, the generator will call the OpenAI Responses API with a
    structured response format bound to `SentimentReportNarrative`.
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        use_llm_mocks: bool | None = None,
    ):
        self.model = model or OPENAI_MODEL
        self.api_key = api_key or OPENAI_API_KEY
        self.use_llm_mocks = USE_LLM_MOCKS if use_llm_mocks is None else use_llm_mocks
        self._client = None

    async def generate(
        self,
        context: SentimentAnalysisInput,
        market_trend: MarketTrend,
        signal: Signal,
    ) -> SentimentReportNarrative:
        if self.use_llm_mocks or not self.api_key:
            return self._mock_narrative(context, market_trend, signal)

        try:
            client = self._lazy_client()
            response = await client.responses.parse(  # type: ignore[attr-defined]
                model=self.model,
                input=self._build_prompt(context, market_trend, signal),
                response_format=SentimentReportNarrative,
                temperature=0.2,
            )
            parsed: Any = getattr(response, "output_parsed", None)
            if parsed:
                return parsed
        except Exception:
            # Fall back to deterministic narrative on any SDK failure.
            return self._mock_narrative(context, market_trend, signal)

        return self._mock_narrative(context, market_trend, signal)

    def _lazy_client(self):
        if self._client is None:
            from openai import (
                AsyncOpenAI,
            )  # Lazy import to avoid dependency during tests

            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    def _build_prompt(
        self,
        context: SentimentAnalysisInput,
        market_trend: MarketTrend,
        signal: Signal,
    ) -> list[dict[str, str]]:
        breakdown_payload = (
            context.breakdown.model_dump(mode="json", exclude_none=True)
            if context.breakdown
            else {}
        )
        drivers_payload = [
            driver.model_dump(mode="json", exclude_none=True)
            for driver in (context.top_drivers or [])
        ]
        numeric_payload = {
            "sentiment_score": context.overall_sentiment_score,
            "relevance_score": context.overall_relevance_score,
            "impact_score": context.overall_impact_score,
            "market_trend": market_trend.value,
            "signal": signal.value,
            "window": context.time_window.value if context.time_window else None,
        }

        system_message = (
            """
            You are an analyst producing concise monitoring guidance for downstream agents.
            Only restate numbers that are provided in the input. Keep language crisp and avoid advice-like phrasing.
            """
        ).strip()
        user_message = (
            f"""
            Ticker: {context.ticker}. Deterministic metrics: {numeric_payload}.
            Breakdown: {breakdown_payload}. Top drivers: {drivers_payload}.
            Return a JSON object matching the SentimentReportNarrative schema with short, actionable bullet strings.
            """
        ).strip()
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

    def _mock_narrative(
        self,
        context: SentimentAnalysisInput,
        market_trend: MarketTrend,
        signal: Signal,
    ) -> SentimentReportNarrative:
        if not context.contents:
            return SentimentReportNarrative(
                summary=f"No recent data available for {context.ticker}.",
                reasoning="Sources returned no sentiment-bearing content in the requested window.",
                highlights=[],
                recommendations=[
                    f"Collect additional news for {context.ticker} and retry analysis.",
                    "Monitor major wires for fresh headlines in the next interval.",
                ],
            )

        highlights = [
            c.content.title for c in context.top_drivers or [] if c.content.title
        ]
        return SentimentReportNarrative(
            summary=f"{context.ticker} sentiment is {market_trend.value} with signal {signal.value}.",
            reasoning=(
                f"Derived from {len(context.contents)} scored items with weighted sentiment {context.overall_sentiment_score}."
            ),
            highlights=highlights,
            recommendations=[
                f"Track how new {context.ticker} headlines affect the current {market_trend.value} tone.",
                "Flag large swings in impact or relevance before acting on this signal.",
            ],
        )
