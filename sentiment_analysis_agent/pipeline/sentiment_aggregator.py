"""Deterministic sentiment aggregation logic."""

from sentiment_analysis_agent.models.sentiment_analysis_models import (
    SentimentBreakdown,
    SentimentContentScore,
)


class SentimentAggregator:
    """Aggregates sentiment metrics from a list of scored content items."""

    @staticmethod
    def aggregate(contents: list[SentimentContentScore]) -> dict:
        """Compute aggregate metrics from a list of scored items.

        Args:
            contents: List of scored content items.

        Returns:
            Dictionary containing aggregated metrics matching the fields expected
            by SentimentAnalysisInput (breakdown, overall_sentiment_score, etc.)
            and SentimentReport.
        """
        if not contents:
            return {
                "breakdown": SentimentBreakdown(
                    positive=0,
                    negative=0,
                    neutral=0,
                    positive_ratio=0.0,
                    negative_ratio=0.0,
                    neutral_ratio=0.0,
                ),
                "overall_sentiment_score": 0.0,
                "overall_relevance_score": 0.0,
                "overall_impact_score": 0.0,
                "top_drivers": [],
            }

        # 1. Compute Breakdown
        positive = sum(1 for c in contents if c.sentiment_score > 0)
        negative = sum(1 for c in contents if c.sentiment_score < 0)
        neutral = sum(1 for c in contents if c.sentiment_score == 0)

        # 2. Compute Weighted Scores
        # We weight by (relevance * impact) to prioritize significant news
        # If all weights are 0, we fall back to simple average
        total_weight = sum(c.weight() for c in contents)

        if total_weight > 0:
            weighted_sentiment_sum = sum(
                c.sentiment_score * c.weight() for c in contents
            )
            overall_sentiment = weighted_sentiment_sum / total_weight
        else:
            # Fallback to simple average if no items have impact/relevance weight
            overall_sentiment = sum(c.sentiment_score for c in contents) / len(contents)

        # Relevance and Impact are averaged normally (simple mean) to reflect the "average quality" of the signal
        # Alternatively, we could weight them, but simple average is often clearer.
        overall_relevance = sum(c.relevance_score for c in contents) / len(contents)
        overall_impact = sum(c.impact_score for c in contents) / len(contents)

        # 3. Top Drivers
        # Sort by weight desc, then by date desc
        sorted_contents = sorted(
            contents,
            key=lambda c: (c.weight(), c.scored_at),
            reverse=True,
        )
        # Take top 5 as drivers
        top_drivers = sorted_contents[:5]

        return {
            "breakdown": SentimentBreakdown(
                positive=positive,
                negative=negative,
                neutral=neutral,
                # Ratios are auto-computed by the model validator if left None,
                # but we can pass them explicitly to be safe or rely on the validator.
                # Let's rely on the validator to compute ratios from counts.
                positive_ratio=None,
                negative_ratio=None,
                neutral_ratio=None,
            ),
            "overall_sentiment_score": round(overall_sentiment, 2),
            "overall_relevance_score": round(overall_relevance, 2),
            "overall_impact_score": round(overall_impact, 2),
            "top_drivers": top_drivers,
        }
