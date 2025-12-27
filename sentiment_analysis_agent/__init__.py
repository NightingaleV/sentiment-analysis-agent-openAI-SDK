"""Sentiment Analysis Agent - Agentic stock analysis system.

This package provides sentiment analysis capabilities for stock market news
using pre-trained financial sentiment models.
"""

from sentiment_analysis_agent.pipeline import (
    SentimentScoringPipeline,
    ScoringConfig,
    ModelType,
    Device,
)

__all__ = [
    "SentimentScoringPipeline",
    "ScoringConfig",
    "ModelType",
    "Device",
]