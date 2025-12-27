"""Unit tests for sentiment scoring pipeline."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sentiment_analysis_agent.models.sentiment_analysis_models import SentimentContent
from sentiment_analysis_agent.pipeline import (
    Device,
    ModelType,
    ScoringConfig,
    SentimentScoringPipeline,
)
from sentiment_analysis_agent.pipeline.models import (
    DistilRobertaFineTunedStrategy,
    ModelFactory,
    SentimentResult,
)


@pytest.fixture
def sample_content():
    """Create a sample SentimentContent for testing."""
    return SentimentContent(
        ticker="AAPL",
        title="Apple announces record-breaking quarterly earnings",
        summary="Apple Inc. reported its best quarter ever with revenues exceeding expectations.",
        body="Apple Inc. (AAPL) has announced record-breaking quarterly earnings, "
        "beating analyst expectations. The company's CEO attributed the success to strong iPhone sales.",
        published_at=datetime.now(timezone.utc) - timedelta(hours=2),
        source="test_source",
    )


@pytest.fixture
def negative_content():
    """Create a negative SentimentContent for testing."""
    return SentimentContent(
        ticker="TSLA",
        title="Tesla announces major production setbacks",
        summary="Tesla warns investors about significant production cuts driven by supply chain disruptions.",
        body="Tesla Inc. (TSLA) reported severe manufacturing challenges, citing critical component shortages and "
        "unexpected factory downtime that will lower output guidance for the upcoming quarter.",
        published_at=datetime.now(timezone.utc) - timedelta(hours=4),
        source="test_source",
    )


@pytest.fixture
def slightly_negative_content():
    """Create a slightly negative SentimentContent for testing."""
    return SentimentContent(
        ticker="MSFT",
        title="Microsoft trims guidance on softer cloud demand",
        summary="Microsoft lowers revenue outlook due to temporary slowdown in enterprise cloud spending growth.",
        body="Microsoft Corp. (MSFT) modestly cut its quarterly guidance, citing a pause in migrations from several "
        "large clients and higher optimization activity that will ease in the second half of the year.",
        published_at=datetime.now(timezone.utc) - timedelta(days=1),
        source="test_source",
    )


@pytest.fixture
def slightly_positive_content():
    """Create a slightly positive SentimentContent for testing."""
    return SentimentContent(
        ticker="GOOGL",
        title="Alphabet expands AI partnerships with regional telcos",
        summary="Alphabet signs new agreements to integrate AI tools with telecom partners across Asia-Pacific.",
        body="Alphabet Inc. (GOOGL) announced a series of regional partnerships aimed at embedding Vertex AI "
        "capabilities into telecom workflows, signaling steady adoption without immediate revenue impact.",
        published_at=datetime.now(timezone.utc) - timedelta(hours=6),
        source="test_source",
    )


@pytest.fixture
def old_content():
    """Create an old SentimentContent for testing freshness scoring."""
    return SentimentContent(
        ticker="TSLA",
        title="Tesla stock update",
        summary="Tesla continues to innovate.",
        published_at=datetime.now(timezone.utc) - timedelta(days=14),  # 2 weeks old
        source="test_source",
    )


class TestScoringConfig:
    """Tests for ScoringConfig validation."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ScoringConfig()
        assert config.model_type == ModelType.DISTILROBERTA_FINETUNED
        assert config.device is None  # Auto-detect
        assert config.max_length == 512
        assert config.batch_size == 8

    def test_invalid_max_length(self):
        """Test validation of max_length parameter."""
        with pytest.raises(ValueError, match="max_length must be positive"):
            ScoringConfig(max_length=0)

    def test_invalid_batch_size(self):
        """Test validation of batch_size parameter."""
        with pytest.raises(ValueError, match="batch_size must be positive"):
            ScoringConfig(batch_size=-1)

    def test_invalid_truncation_strategy(self):
        """Test validation of truncation_strategy parameter."""
        with pytest.raises(ValueError, match="truncation_strategy must be"):
            ScoringConfig(truncation_strategy="invalid")

    def test_invalid_weights_sum(self):
        """Test validation that weights sum to 1.0."""
        with pytest.raises(ValueError, match="relevance weights must sum to 1.0"):
            ScoringConfig(relevance_ticker_weight=0.5, relevance_length_weight=0.4)


class TestSentimentModelStrategy:
    """Tests for model strategy classes."""

    @patch("sentiment_analysis_agent.pipeline.models.torch")
    def test_device_detection_mps(self, mock_torch):
        """Test device detection for Apple Silicon (MPS)."""
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.cuda.is_available.return_value = False

        strategy = DistilRobertaFineTunedStrategy()
        assert strategy.device == Device.MPS

    @patch("sentiment_analysis_agent.pipeline.models.torch")
    def test_device_detection_cuda(self, mock_torch):
        """Test device detection for CUDA GPUs."""
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = True

        strategy = DistilRobertaFineTunedStrategy()
        assert strategy.device == Device.CUDA

    @patch("sentiment_analysis_agent.pipeline.models.torch")
    def test_device_detection_cpu(self, mock_torch):
        """Test device detection fallback to CPU."""
        mock_torch.backends.mps.is_available.return_value = False
        mock_torch.cuda.is_available.return_value = False

        strategy = DistilRobertaFineTunedStrategy()
        assert strategy.device == Device.CPU

    def test_model_name(self):
        """Test model name property."""
        strategy = DistilRobertaFineTunedStrategy()
        assert strategy.model_name == ModelType.DISTILROBERTA_FINETUNED.value

    def test_label_mapping(self):
        """Test label to sentiment score mapping."""
        strategy = DistilRobertaFineTunedStrategy()
        assert strategy.label_mapping["positive"] == 1.0
        assert strategy.label_mapping["negative"] == -1.0
        assert strategy.label_mapping["neutral"] == 0.0


class TestModelFactory:
    """Tests for ModelFactory singleton management."""

    def test_get_strategy_creates_instance(self):
        """Test factory creates strategy instances."""
        ModelFactory.clear_cache()
        strategy = ModelFactory.get_strategy(ModelType.DISTILROBERTA_FINETUNED)
        assert isinstance(strategy, DistilRobertaFineTunedStrategy)

    def test_get_strategy_returns_cached(self):
        """Test factory returns cached instances."""
        ModelFactory.clear_cache()
        strategy1 = ModelFactory.get_strategy(ModelType.DISTILROBERTA_FINETUNED)
        strategy2 = ModelFactory.get_strategy(ModelType.DISTILROBERTA_FINETUNED)
        assert strategy1 is strategy2  # Same instance

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        ModelFactory.clear_cache()
        strategy1 = ModelFactory.get_strategy(ModelType.DISTILROBERTA_FINETUNED)
        ModelFactory.clear_cache()
        strategy2 = ModelFactory.get_strategy(ModelType.DISTILROBERTA_FINETUNED)
        assert strategy1 is not strategy2  # Different instances


class TestSentimentScoringPipeline:
    """Tests for the main SentimentScoringPipeline class."""

    @pytest.fixture
    def mock_model_strategy(self):
        """Create a mock model strategy for testing."""
        strategy = MagicMock()
        strategy.model_name = "mock-model"
        strategy.predict = AsyncMock()
        return strategy

    @pytest.fixture
    def pipeline_with_mock(self, mock_model_strategy):
        """Create pipeline with mocked model strategy."""
        with patch.object(
            ModelFactory, "get_strategy", return_value=mock_model_strategy
        ):
            pipeline = SentimentScoringPipeline()
            pipeline._model_strategy = mock_model_strategy
            return pipeline

    def test_pipeline_initialization(self):
        """Test pipeline initialization with default config."""
        pipeline = SentimentScoringPipeline()
        assert pipeline.config is not None
        assert pipeline.config.model_type == ModelType.DISTILROBERTA_FINETUNED

    def test_pipeline_custom_config(self):
        """Test pipeline initialization with custom config."""
        config = ScoringConfig(batch_size=16, max_length=256)
        pipeline = SentimentScoringPipeline(config)
        assert pipeline.config.batch_size == 16
        assert pipeline.config.max_length == 256

    @pytest.mark.asyncio
    async def test_score_single_content(self, pipeline_with_mock, sample_content):
        """Test scoring a single positive content item."""
        mock_strategy = pipeline_with_mock._model_strategy
        mock_strategy.predict = AsyncMock(
            return_value=[
                SentimentResult(label="positive", score=0.95, sentiment_score=1.0)
            ]
        )

        scored = await pipeline_with_mock.score(sample_content)

        assert scored.content == sample_content
        assert scored.sentiment_score == 1.0
        assert scored.confidence == 0.95
        assert 0 <= scored.relevance_score <= 1
        assert 0 <= scored.impact_score <= 1
        assert scored.reasoning is not None
        assert scored.model_name == "mock-model"

    @pytest.mark.asyncio
    async def test_score_single_negative_content(
        self, pipeline_with_mock, negative_content
    ):
        """Test scoring a single negative content item."""
        mock_strategy = pipeline_with_mock._model_strategy
        mock_strategy.predict = AsyncMock(
            return_value=[
                SentimentResult(label="negative", score=0.87, sentiment_score=-1.0)
            ]
        )

        scored = await pipeline_with_mock.score(negative_content)

        assert scored.content == negative_content
        assert scored.sentiment_score == -1.0
        assert scored.confidence == 0.87
        assert 0 <= scored.relevance_score <= 1
        assert 0 <= scored.impact_score <= 1
        assert scored.reasoning is not None
        assert scored.model_name == "mock-model"

    @pytest.mark.asyncio
    async def test_score_single_slightly_negative_content(
        self, pipeline_with_mock, slightly_negative_content
    ):
        """Test scoring a slightly negative content item."""
        mock_strategy = pipeline_with_mock._model_strategy
        mock_strategy.predict = AsyncMock(
            return_value=[
                SentimentResult(label="negative", score=0.62, sentiment_score=-0.25)
            ]
        )

        scored = await pipeline_with_mock.score(slightly_negative_content)

        assert scored.content == slightly_negative_content
        assert scored.sentiment_score == -0.25
        assert scored.confidence == 0.62
        assert 0 <= scored.relevance_score <= 1
        assert 0 <= scored.impact_score <= 1
        assert scored.reasoning is not None
        assert scored.model_name == "mock-model"

    @pytest.mark.asyncio
    async def test_score_single_slightly_positive_content(
        self, pipeline_with_mock, slightly_positive_content
    ):
        """Test scoring a slightly positive content item."""
        mock_strategy = pipeline_with_mock._model_strategy
        mock_strategy.predict = AsyncMock(
            return_value=[
                SentimentResult(label="positive", score=0.68, sentiment_score=0.35)
            ]
        )

        scored = await pipeline_with_mock.score(slightly_positive_content)

        assert scored.content == slightly_positive_content
        assert scored.sentiment_score == 0.35
        assert scored.confidence == 0.68
        assert 0 <= scored.relevance_score <= 1
        assert 0 <= scored.impact_score <= 1
        assert scored.reasoning is not None
        assert scored.model_name == "mock-model"

    @pytest.mark.asyncio
    async def test_score_batch(self, pipeline_with_mock, sample_content, old_content):
        """Test scoring multiple content items in batch."""
        mock_strategy = pipeline_with_mock._model_strategy
        mock_strategy.predict = AsyncMock(
            return_value=[
                SentimentResult(label="positive", score=0.95, sentiment_score=1.0),
                SentimentResult(label="negative", score=0.85, sentiment_score=-1.0),
            ]
        )

        scored_batch = await pipeline_with_mock.score_batch(
            [sample_content, old_content]
        )

        assert len(scored_batch) == 2
        assert scored_batch[0].sentiment_score == 1.0
        assert scored_batch[1].sentiment_score == -1.0

    @pytest.mark.asyncio
    async def test_score_empty_batch(self, pipeline_with_mock):
        """Test scoring an empty batch."""
        scored_batch = await pipeline_with_mock.score_batch([])
        assert scored_batch == []

    def test_preprocess_text_combines_fields(self, pipeline_with_mock, sample_content):
        """Test text preprocessing combines title, summary, and body."""
        text = pipeline_with_mock._preprocess_text(sample_content)
        assert "Apple announces record-breaking" in text
        assert "best quarter ever" in text
        assert "strong iPhone sales" in text

    def test_preprocess_text_handles_none(self, pipeline_with_mock):
        """Test text preprocessing handles None values gracefully."""
        content = SentimentContent(
            ticker="AAPL", title="Title only", summary=None, body=None
        )
        text = pipeline_with_mock._preprocess_text(content)
        assert text == "Title only"

    def test_smart_truncate_prioritizes_title_summary(self, pipeline_with_mock):
        """Test smart truncation prioritizes title and summary over body."""
        long_body = "x" * 10000
        content = SentimentContent(
            ticker="AAPL",
            title="Important Title",
            summary="Key Summary",
            body=long_body,
            source="test",
        )

        text = pipeline_with_mock._smart_truncate(content)
        assert "Important Title" in text
        assert "Key Summary" in text
        assert len(text) <= pipeline_with_mock.config.max_length * 4

    def test_calculate_relevance_score_ticker_mentions(
        self, pipeline_with_mock, sample_content
    ):
        """Test relevance score increases with ticker mentions."""
        text = pipeline_with_mock._preprocess_text(sample_content)
        relevance = pipeline_with_mock._calculate_relevance_score(sample_content, text)

        # Content mentions AAPL multiple times
        assert relevance > pipeline_with_mock.config.min_relevance_score

    def test_calculate_relevance_score_no_ticker(self, pipeline_with_mock):
        """Test relevance score with no ticker mentions."""
        content = SentimentContent(
            ticker="AAPL", title="General market news", source="test"
        )
        text = pipeline_with_mock._preprocess_text(content)
        relevance = pipeline_with_mock._calculate_relevance_score(content, text)

        # Should still have minimum relevance
        assert relevance >= pipeline_with_mock.config.min_relevance_score

    def test_calculate_impact_score_freshness(
        self, pipeline_with_mock, sample_content, old_content
    ):
        """Test impact score is higher for fresh content."""
        fresh_text = pipeline_with_mock._preprocess_text(sample_content)
        old_text = pipeline_with_mock._preprocess_text(old_content)

        fresh_impact = pipeline_with_mock._calculate_impact_score(
            sample_content, fresh_text
        )
        old_impact = pipeline_with_mock._calculate_impact_score(old_content, old_text)

        assert fresh_impact > old_impact

    def test_calculate_freshness_score(self, pipeline_with_mock):
        """Test freshness score calculation."""
        now = datetime.now(timezone.utc)
        very_fresh = now - timedelta(hours=1)
        fresh = now - timedelta(days=1)
        old = now - timedelta(days=7)
        very_old = now - timedelta(days=14)

        very_fresh_score = pipeline_with_mock._calculate_freshness_score(very_fresh)
        fresh_score = pipeline_with_mock._calculate_freshness_score(fresh)
        old_score = pipeline_with_mock._calculate_freshness_score(old)
        very_old_score = pipeline_with_mock._calculate_freshness_score(very_old)

        assert very_fresh_score > fresh_score > old_score > very_old_score

    def test_calculate_freshness_score_none(self, pipeline_with_mock):
        """Test freshness score with None published_at."""
        score = pipeline_with_mock._calculate_freshness_score(None)
        assert score == 0.5  # Default value

    def test_count_ticker_mentions(self, pipeline_with_mock):
        """Test ticker mention counting."""
        text = "AAPL announced earnings. AAPL stock rose. Investors love AAPL."
        count = pipeline_with_mock._count_ticker_mentions("AAPL", text)
        assert count == 3

    def test_count_ticker_mentions_case_insensitive(self, pipeline_with_mock):
        """Test ticker counting is case-insensitive."""
        text = "aapl announced earnings. AAPL stock rose."
        count = pipeline_with_mock._count_ticker_mentions("AAPL", text)
        assert count == 2

    def test_count_ticker_mentions_word_boundary(self, pipeline_with_mock):
        """Test ticker counting respects word boundaries."""
        text = "APPLY is not AAPL but AAPL is mentioned."
        count = pipeline_with_mock._count_ticker_mentions("AAPL", text)
        assert count == 2  # Should not match APPLY

    def test_build_reasoning(self, pipeline_with_mock, sample_content):
        """Test reasoning string generation."""
        sentiment_result = SentimentResult(
            label="positive", score=0.95, sentiment_score=1.0
        )
        reasoning = pipeline_with_mock._build_reasoning(
            sample_content, sentiment_result, 0.8, 0.7
        )

        assert "Sentiment: positive" in reasoning
        assert "confidence: 0.95" in reasoning
        assert "Relevance: 0.80" in reasoning
        assert "Impact: 0.70" in reasoning
        assert "AAPL" in reasoning


@pytest.mark.integration
class TestSentimentPipelineIntegration:
    """Integration tests with real models (slow, marked for optional execution)."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_pipeline_with_real_model(self, sample_content):
        """Test pipeline with actual HuggingFace model (slow test)."""
        config = ScoringConfig(model_type=ModelType.DISTILROBERTA_FINETUNED)
        pipeline = SentimentScoringPipeline(config)

        scored = await pipeline.score(sample_content)

        # Verify all fields are populated correctly
        assert scored.content == sample_content
        assert -1 <= scored.sentiment_score <= 1
        assert 0 <= scored.relevance_score <= 1
        assert 0 <= scored.impact_score <= 1
        assert 0 <= scored.confidence <= 1
        assert scored.reasoning is not None
        assert scored.model_name == ModelType.DISTILROBERTA_FINETUNED.value
