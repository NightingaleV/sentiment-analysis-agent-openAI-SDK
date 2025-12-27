"""Sentiment scoring pipeline for transforming raw content into scored content."""

import re
from datetime import datetime, timezone

from sentiment_analysis_agent.models.sentiment_analysis_models import SentimentContent, SentimentContentScore
from sentiment_analysis_agent.pipeline.config import ScoringConfig
from sentiment_analysis_agent.pipeline.models import ModelFactory


class SentimentScoringPipeline:
    """Pipeline for scoring raw sentiment content using ML models and heuristics.

    This pipeline transforms SentimentContent (raw text) into SentimentContentScore
    by applying:
    1. Sentiment classification using pre-trained financial models
    2. Relevance scoring based on ticker mentions and content quality
    3. Impact scoring based on content freshness and length

    Example:
        ```python
        config = ScoringConfig()
        pipeline = SentimentScoringPipeline(config)

        # Score single content
        raw_content = SentimentContent(ticker="AAPL", title="Apple hits new high", ...)
        scored = await pipeline.score(raw_content)

        # Score batch
        scored_batch = await pipeline.score_batch([content1, content2, ...])
        ```
    """

    def __init__(self, config: ScoringConfig | None = None):
        """Initialize the scoring pipeline.

        Args:
            config: Scoring configuration. Uses defaults if None.
        """
        self.config = config or ScoringConfig()
        self._model_strategy = ModelFactory.get_strategy(self.config.model_type, self.config.device)

    async def score(self, content: SentimentContent) -> SentimentContentScore:
        """Score a single content item.

        Args:
            content: Raw sentiment content to score

        Returns:
            Scored content with sentiment, relevance, and impact scores
        """
        results = await self.score_batch([content])
        return results[0]

    async def score_batch(self, contents: list[SentimentContent]) -> list[SentimentContentScore]:
        """Score a batch of content items efficiently.

        Args:
            contents: List of raw sentiment content to score

        Returns:
            List of scored content items (same order as input)
        """
        if not contents:
            return []

        # Step 1: Preprocess all texts
        preprocessed_texts = [self._preprocess_text(c) for c in contents]

        # Step 2: Get sentiment predictions from model (batch inference)
        sentiment_results = await self._model_strategy.predict(preprocessed_texts)

        # Step 3: Compute heuristic scores and build final results
        scored_contents = []
        for content, text, sentiment_result in zip(contents, preprocessed_texts, sentiment_results):
            # Calculate relevance score (ticker mentions + content quality)
            relevance_score = self._calculate_relevance_score(content, text)

            # Calculate impact score (freshness + length)
            impact_score = self._calculate_impact_score(content, text)

            # Build reasoning string
            reasoning = self._build_reasoning(content, sentiment_result, relevance_score, impact_score)

            # Create scored content
            scored = SentimentContentScore(
                content=content,
                sentiment_score=sentiment_result.sentiment_score,
                relevance_score=relevance_score,
                impact_score=impact_score,
                confidence=sentiment_result.score,
                reasoning=reasoning,
                scored_at=datetime.now(timezone.utc),
                model_name=self._model_strategy.model_name,
            )
            scored_contents.append(scored)

        return scored_contents

    def _preprocess_text(self, content: SentimentContent) -> str:
        """Preprocess and combine content fields into a single text.

        Args:
            content: Raw sentiment content

        Returns:
            Combined and truncated text ready for model inference
        """
        # Combine title, summary, and body with proper handling of None values
        parts = []
        if content.title:
            parts.append(content.title.strip())
        if content.summary:
            parts.append(content.summary.strip())
        if content.body:
            parts.append(content.body.strip())

        combined_text = " ".join(parts)

        # Handle truncation strategy
        if self.config.truncation_strategy == "smart":
            # Smart truncation: prioritize title and summary over body
            return self._smart_truncate(content)
        else:
            # Head truncation: take first N characters
            return combined_text[: self.config.max_length * 4]  # Rough char estimate (4 chars per token)

    def _smart_truncate(self, content: SentimentContent) -> str:
        """Smart truncation that prioritizes title and summary.

        Args:
            content: Raw sentiment content

        Returns:
            Truncated text that fits within token limits
        """
        # Estimate: ~4 characters per token for English text
        max_chars = self.config.max_length * 4

        # Always include title
        parts = []
        if content.title:
            parts.append(content.title.strip())

        # Try to include summary
        if content.summary:
            parts.append(content.summary.strip())

        # Add body if there's room
        combined = " ".join(parts)
        if content.body and len(combined) < max_chars:
            remaining_chars = max_chars - len(combined) - 1  # -1 for space
            body_excerpt = content.body.strip()[:remaining_chars]
            parts.append(body_excerpt)

        return " ".join(parts)[:max_chars]

    def _calculate_relevance_score(self, content: SentimentContent, text: str) -> float:
        """Calculate relevance score based on ticker mentions and content quality.

        Args:
            content: Original content object
            text: Preprocessed text

        Returns:
            Relevance score in range [min_relevance_score, 1.0]
        """
        # Component 1: Ticker mention frequency (normalized)
        ticker_count = self._count_ticker_mentions(content.ticker, text)
        ticker_score = min(1.0, ticker_count / 5)  # Cap at 5 mentions = 1.0

        # Component 2: Content length quality (longer = more relevant, up to a point)
        text_length = len(text)
        length_score = min(1.0, text_length / 1000)  # Cap at 1000 chars = 1.0

        # Weighted combination
        relevance = (
            self.config.relevance_ticker_weight * ticker_score + self.config.relevance_length_weight * length_score
        )

        # Apply floor
        return max(self.config.min_relevance_score, relevance)

    def _calculate_impact_score(self, content: SentimentContent, text: str) -> float:
        """Calculate impact score based on freshness and content length.

        Args:
            content: Original content object
            text: Preprocessed text

        Returns:
            Impact score in range [min_impact_score, 1.0]
        """
        # Component 1: Freshness (newer content has higher impact)
        freshness_score = self._calculate_freshness_score(content.published_at)

        # Component 2: Content length (longer content has higher potential impact)
        text_length = len(text)
        length_score = min(1.0, text_length / 2000)  # Cap at 2000 chars = 1.0

        # Weighted combination
        impact = self.config.impact_freshness_weight * freshness_score + self.config.impact_length_weight * length_score

        # Apply floor
        return max(self.config.min_impact_score, impact)

    def _calculate_freshness_score(self, published_at: datetime | None) -> float:
        """Calculate freshness score based on publication date.

        Args:
            published_at: Publication timestamp (UTC)

        Returns:
            Freshness score in range [0, 1.0]
        """
        if published_at is None:
            return 0.5  # Default if unknown

        now = datetime.now(timezone.utc)
        age_hours = (now - published_at).total_seconds() / 3600

        # Decay function: exponential decay over 7 days
        # Fresh (< 1 day): 1.0
        # 1 week old: ~0.5
        # 2 weeks old: ~0.25
        decay_rate = 0.1  # Controls how fast impact decays
        freshness = max(0.0, 1.0 - (age_hours / 168) * decay_rate)  # 168 hours = 1 week

        return min(1.0, freshness)

    def _count_ticker_mentions(self, ticker: str, text: str) -> int:
        """Count how many times the ticker appears in text.

        Args:
            ticker: Stock ticker symbol
            text: Text to search

        Returns:
            Number of ticker mentions (case-insensitive)
        """
        # Use word boundary regex to avoid partial matches
        pattern = rf"\b{re.escape(ticker)}\b"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return len(matches)

    def _build_reasoning(
        self, content: SentimentContent, sentiment_result, relevance_score: float, impact_score: float
    ) -> str:
        """Build human-readable reasoning string.

        Args:
            content: Original content
            sentiment_result: Model prediction result
            relevance_score: Calculated relevance score
            impact_score: Calculated impact score

        Returns:
            Reasoning string explaining the scores
        """
        parts = [
            f"Sentiment: {sentiment_result.label} (confidence: {sentiment_result.score:.2f})",
            f"Relevance: {relevance_score:.2f} (ticker mentions + content quality)",
            f"Impact: {impact_score:.2f} (freshness + content depth)",
        ]

        # Add context about ticker mentions
        text = self._preprocess_text(content)
        ticker_count = self._count_ticker_mentions(content.ticker, text)
        if ticker_count > 0:
            parts.append(f"Ticker '{content.ticker}' mentioned {ticker_count}x")

        return "; ".join(parts)
