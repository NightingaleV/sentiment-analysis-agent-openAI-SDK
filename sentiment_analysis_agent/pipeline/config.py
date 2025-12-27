"""Configuration for the sentiment scoring pipeline."""

from dataclasses import dataclass
from enum import Enum


class ModelType(str, Enum):
    """Available sentiment model types."""

    DISTILROBERTA_FINETUNED = "msr2903/mrm8488-distilroberta-fine-tuned-financial-sentiment"
    DISTILROBERTA_BASE = "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"


class Device(str, Enum):
    """Computing device options for model inference."""

    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Silicon GPU acceleration


@dataclass
class ScoringConfig:
    """Configuration parameters for sentiment scoring pipeline.

    Attributes:
        model_type: Which pre-trained model to use for sentiment classification
        device: Computing device (cpu/cuda/mps) - auto-detected if None
        max_length: Maximum token length for model input (distilroberta default: 512)
        batch_size: Number of content items to process in parallel
        truncation_strategy: How to handle text exceeding max_length ('smart' or 'head')
        relevance_ticker_weight: Weight for ticker mentions in relevance calculation (0..1)
        relevance_length_weight: Weight for content length in relevance calculation (0..1)
        impact_freshness_weight: Weight for content freshness in impact calculation (0..1)
        impact_length_weight: Weight for content length in impact calculation (0..1)
        min_relevance_score: Minimum relevance score for any content (floor value)
        min_impact_score: Minimum impact score for any content (floor value)
    """

    model_type: ModelType = ModelType.DISTILROBERTA_FINETUNED
    device: Device | None = None  # Auto-detect if None
    max_length: int = 512
    batch_size: int = 8
    truncation_strategy: str = "smart"  # 'smart' or 'head'

    # Heuristic weights for relevance score calculation
    relevance_ticker_weight: float = 0.7
    relevance_length_weight: float = 0.3

    # Heuristic weights for impact score calculation
    impact_freshness_weight: float = 0.6
    impact_length_weight: float = 0.4

    # Minimum floor values
    min_relevance_score: float = 0.1
    min_impact_score: float = 0.1

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.max_length <= 0:
            raise ValueError("max_length must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.truncation_strategy not in ("smart", "head"):
            raise ValueError("truncation_strategy must be 'smart' or 'head'")

        # Validate weights sum to 1.0
        relevance_sum = self.relevance_ticker_weight + self.relevance_length_weight
        if not (0.99 <= relevance_sum <= 1.01):
            raise ValueError(f"relevance weights must sum to 1.0, got {relevance_sum}")

        impact_sum = self.impact_freshness_weight + self.impact_length_weight
        if not (0.99 <= impact_sum <= 1.01):
            raise ValueError(f"impact weights must sum to 1.0, got {impact_sum}")

        # Validate score floors
        if not (0 <= self.min_relevance_score <= 1):
            raise ValueError("min_relevance_score must be in range [0, 1]")
        if not (0 <= self.min_impact_score <= 1):
            raise ValueError("min_impact_score must be in range [0, 1]")
