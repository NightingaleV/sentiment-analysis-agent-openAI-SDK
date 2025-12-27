"""Sentiment scoring pipeline module.

This module provides tools for transforming raw SentimentContent into
SentimentContentScore using pre-trained financial sentiment models.

Example:
    ```python
    from sentiment_analysis_agent.pipeline import SentimentScoringPipeline, ScoringConfig

    # Create pipeline with default config
    pipeline = SentimentScoringPipeline()

    # Score content
    scored = await pipeline.score(raw_content)
    ```
"""

from sentiment_analysis_agent.pipeline.config import Device, ModelType, ScoringConfig
from sentiment_analysis_agent.pipeline.models import (
    DistilRobertaBaseStrategy,
    DistilRobertaFineTunedStrategy,
    ModelFactory,
    SentimentModelStrategy,
    SentimentResult,
)
from sentiment_analysis_agent.pipeline.sentiment_scorer import SentimentScoringPipeline

__all__ = [
    # Main pipeline
    "SentimentScoringPipeline",
    # Configuration
    "ScoringConfig",
    "ModelType",
    "Device",
    # Model strategies
    "SentimentModelStrategy",
    "DistilRobertaFineTunedStrategy",
    "DistilRobertaBaseStrategy",
    "ModelFactory",
    "SentimentResult",
]
