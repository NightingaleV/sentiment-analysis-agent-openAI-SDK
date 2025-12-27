"""HuggingFace model strategies for sentiment classification."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from sentiment_analysis_agent.pipeline.config import Device, ModelType


@dataclass
class SentimentResult:
    """Result from sentiment model inference.

    Attributes:
        label: Sentiment label (positive/negative/neutral)
        score: Confidence score for the prediction (0..1)
        sentiment_score: Normalized sentiment score (-1..1)
    """

    label: str
    score: float
    sentiment_score: float


class SentimentModelStrategy(ABC):
    """Abstract base class for sentiment model strategies.

    Implements the Strategy pattern to allow different model implementations
    while maintaining a consistent interface for the scoring pipeline.
    """

    def __init__(self, device: Device | None = None):
        """Initialize the model strategy.

        Args:
            device: Computing device (cpu/cuda/mps). Auto-detected if None.
        """
        self.device = self._detect_device() if device is None else Device(device)
        self._model = None
        self._tokenizer = None
        self._pipeline = None

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the HuggingFace model identifier."""
        pass

    @property
    @abstractmethod
    def label_mapping(self) -> dict[str, float]:
        """Return mapping from model labels to sentiment scores (-1..1).

        Returns:
            Dictionary mapping label strings to normalized scores.
            Example: {"negative": -1.0, "neutral": 0.0, "positive": 1.0}
        """
        pass

    def _detect_device(self) -> Device:
        """Auto-detect the best available computing device.

        Returns:
            Device enum value (MPS > CUDA > CPU in order of preference)
        """
        if torch.backends.mps.is_available():
            return Device.MPS
        elif torch.cuda.is_available():
            return Device.CUDA
        return Device.CPU

    def load_model(self) -> None:
        """Load the model and tokenizer into memory.

        This method implements lazy loading - the model is only loaded
        when first needed. Subsequent calls to this method are no-ops.
        """
        if self._pipeline is not None:
            return  # Already loaded

        device_id = -1 if self.device == Device.CPU else 0
        device_str = str(self.device.value)

        # Load tokenizer and model
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)

        # Create HuggingFace pipeline for inference
        self._pipeline = pipeline(
            "text-classification",
            model=self._model,
            tokenizer=self._tokenizer,
            device=device_id,
            return_all_scores=False,  # Return only top prediction
        )

    async def predict(self, texts: list[str]) -> list[SentimentResult]:
        """Predict sentiment for a batch of texts.

        Args:
            texts: List of text strings to classify

        Returns:
            List of SentimentResult objects with predictions
        """
        # Ensure model is loaded
        self.load_model()

        # Run inference in thread pool (blocking I/O)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, self._pipeline, texts)

        # Map results to normalized sentiment scores
        sentiment_results = []
        for result in results:
            label = result["label"].lower()
            confidence = round(float(result["score"]), 2)
            sentiment_score = self.label_mapping.get(label, 0.0)

            sentiment_results.append(SentimentResult(label=label, score=confidence, sentiment_score=sentiment_score))

        return sentiment_results

    async def predict_single(self, text: str) -> SentimentResult:
        """Predict sentiment for a single text.

        Args:
            text: Text string to classify

        Returns:
            SentimentResult with prediction
        """
        results = await self.predict([text])
        return results[0]


class DistilRobertaFineTunedStrategy(SentimentModelStrategy):
    """Strategy for msr2903/mrm8488-distilroberta-fine-tuned-financial-sentiment model.

    This is the primary model - fine-tuned specifically on financial news sentiment.
    It achieves 91.71% accuracy on the evaluation set.
    """

    @property
    def model_name(self) -> str:
        """Return the HuggingFace model identifier."""
        return ModelType.DISTILROBERTA_FINETUNED.value

    @property
    def label_mapping(self) -> dict[str, float]:
        """Map model output labels to sentiment scores.

        Returns:
            Dictionary mapping labels to normalized scores (-1..1)
        """
        return {"negative": -1.0, "neutral": 0.0, "positive": 1.0}


class DistilRobertaBaseStrategy(SentimentModelStrategy):
    """Strategy for mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis model.

    This is the base model - trained on financial_phrasebank dataset.
    It achieves 98.23% accuracy but on a different dataset than the fine-tuned version.
    """

    @property
    def model_name(self) -> str:
        """Return the HuggingFace model identifier."""
        return ModelType.DISTILROBERTA_BASE.value

    @property
    def label_mapping(self) -> dict[str, float]:
        """Map model output labels to sentiment scores.

        Returns:
            Dictionary mapping labels to normalized scores (-1..1)
        """
        return {"negative": -1.0, "neutral": 0.0, "positive": 1.0}


class ModelFactory:
    """Factory for creating sentiment model strategies.

    This class manages singleton instances of loaded models to avoid
    loading the same model multiple times.
    """

    _instances: dict[ModelType, SentimentModelStrategy] = {}

    @classmethod
    def get_strategy(cls, model_type: ModelType, device: Device | None = None) -> SentimentModelStrategy:
        """Get or create a model strategy instance.

        Args:
            model_type: Which model to load
            device: Computing device (auto-detected if None)

        Returns:
            SentimentModelStrategy instance (cached singleton)
        """
        if model_type not in cls._instances:
            if model_type == ModelType.DISTILROBERTA_FINETUNED:
                cls._instances[model_type] = DistilRobertaFineTunedStrategy(device=device)
            elif model_type == ModelType.DISTILROBERTA_BASE:
                cls._instances[model_type] = DistilRobertaBaseStrategy(device=device)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")

        return cls._instances[model_type]

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached model instances."""
        cls._instances.clear()
