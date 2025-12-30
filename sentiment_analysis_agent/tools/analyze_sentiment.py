"""Tool for performing end-to-end sentiment analysis."""

from sentiment_analysis_agent.data_services.base import BaseSentimentSource
from sentiment_analysis_agent.models.sentiment_analysis_models import (
    SentimentAnalysisInput,
    SentimentContent,
    SentimentContentScore,
    TimeWindow,
)
from sentiment_analysis_agent.pipeline.sentiment_aggregator import SentimentAggregator
from sentiment_analysis_agent.pipeline.sentiment_scorer import SentimentScoringPipeline


class AnalyzeSentimentTool:
    """Orchestrates fetching, scoring, and aggregating sentiment data."""

    def __init__(
        self,
        sources: list[BaseSentimentSource],
        scoring_pipeline: SentimentScoringPipeline,
    ):
        """Initialize the tool.

        Args:
            sources: List of data sources to fetch content from.
            scoring_pipeline: Service to score raw content.
        """
        self.sources = sources
        self.scoring_pipeline = scoring_pipeline

    async def run(
        self,
        ticker: str,
        time_window: str = "short",
        limit: int = 50,
    ) -> SentimentAnalysisInput:
        """Execute the sentiment analysis workflow.

        Args:
            ticker: Stock ticker symbol.
            time_window: Time horizon ("short", "medium", "long").
            limit: Maximum number of items to return.

        Returns:
            Fully populated input model with scored contents and aggregates.
        """
        # 1. Resolve Time Window
        try:
            window = TimeWindow(time_window)
        except ValueError:
            window = TimeWindow.SHORT_TERM

        start_time, end_time = window.to_time_range()

        # 2. Fetch from all sources
        raw_contents, scored_contents = await self._fetch_all(
            ticker, start_time, end_time, limit
        )

        # 3. Score Raw Content
        if raw_contents:
            newly_scored = await self.scoring_pipeline.score_batch(raw_contents)
            scored_contents.extend(newly_scored)

        # 4. Deduplicate
        unique_map = {item.content.content_id: item for item in scored_contents}
        unique_scored = list(unique_map.values())

        # 5. Sort by weight
        sorted_contents = sorted(
            unique_scored,
            key=lambda c: (c.weight(), c.scored_at),
            reverse=True,
        )

        # 6. Aggregate (on final set to ensure consistency)
        # We aggregate based on the 'limit' subset to ensure the stats match the data the agent sees.
        final_contents = sorted_contents[:limit]
        aggregates = SentimentAggregator.aggregate(final_contents)

        # 7. Construct Result
        return SentimentAnalysisInput(
            ticker=ticker,
            time_window=window,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            contents=final_contents,
            **aggregates,
        )

    async def _fetch_all(self, ticker, start_time, end_time, limit):
        """Helper to fetch from all sources safely."""
        raw_contents: list[SentimentContent] = []
        scored_contents: list[SentimentContentScore] = []

        for source in self.sources:
            try:
                results = await source.fetch(ticker, start_time, end_time, limit)
                if source.returns_scored:
                    scored_contents.extend(results)  # type: ignore
                else:
                    raw_contents.extend(results)  # type: ignore
            except Exception:  # pylint: disable=broad-exception-caught
                # Graceful degradation: ignore failed sources
                pass

        return raw_contents, scored_contents
