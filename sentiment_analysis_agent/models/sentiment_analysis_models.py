"""Pydantic data models for the sentiment analysis agent."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from enum import StrEnum


from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


def _utcnow() -> datetime:
    """Return timezone-aware UTC timestamp for default factories."""

    return datetime.now(timezone.utc)


def _ensure_utc(value: datetime) -> datetime:
    """Ensure timestamps are timezone-aware UTC."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _ensure_optional_utc(value: datetime | None) -> datetime | None:
    """Ensure optional timestamps are timezone-aware UTC."""

    if value is None:
        return None
    return _ensure_utc(value)


class Signal(StrEnum):
    """Recommendation for trade activity derived from sentiment patterns."""

    STRONG_BUY = "strong buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong sell"

    @classmethod
    def _missing_(cls, value: str):  # type: ignore[override]
        """Provide lenient enum parsing while keeping outputs normalized."""

        normalized = value.lower().strip()
        for member in cls:
            if member.value == normalized:
                return member
        allowed = ", ".join(m.value for m in cls)
        raise ValueError(f"Invalid Signal value: {value!r}. Must be one of: {allowed}")


class MarketTrend(StrEnum):
    """Qualitative description of current market tone around a ticker."""

    GREEDY = "greedy"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    FEARFUL = "fearful"

    @classmethod
    def _missing_(cls, value: str):  # type: ignore[override]
        """Provide lenient enum parsing while keeping outputs normalized."""

        normalized = value.lower().strip()
        for member in cls:
            if member.value == normalized:
                return member
        allowed = ", ".join(m.value for m in cls)
        raise ValueError(
            f"Invalid MarketTrend value: {value!r}. Must be one of: {allowed}"
        )


class SourceType(StrEnum):
    """High-level categories for sentiment sources (news, social, etc.)."""

    NEWS = "news"
    SOCIAL = "social"
    FORUM = "forum"
    BLOG = "blog"
    RESEARCH = "research"
    OTHER = "other"

    @classmethod
    def _missing_(cls, value: str):  # type: ignore[override]
        """Provide lenient enum parsing while keeping outputs normalized."""

        normalized = value.lower().strip()
        for member in cls:
            if member.value == normalized:
                return member
        allowed = ", ".join(m.value for m in cls)
        raise ValueError(
            f"Invalid SourceType value: {value!r}. Must be one of: {allowed}"
        )


class TimeWindow(StrEnum):
    """Categorical time windows used to fetch and aggregate content."""

    SHORT_TERM = "short"
    MEDIUM_TERM = "medium"
    LONG_TERM = "long"

    @classmethod
    def _missing_(cls, value: str):  # type: ignore[override]
        """Provide lenient parsing for labels like 'short term' or 'medium-term'."""

        normalized = value.lower().replace("-", " ").strip()
        normalized = normalized.replace(" term", "").strip()
        aliases = {
            "short": cls.SHORT_TERM,
            "shortterm": cls.SHORT_TERM,
            "medium": cls.MEDIUM_TERM,
            "mediumterm": cls.MEDIUM_TERM,
            "long": cls.LONG_TERM,
            "longterm": cls.LONG_TERM,
        }
        mapped = aliases.get(normalized.replace(" ", ""))
        if mapped:
            return mapped
        allowed = ", ".join(m.value for m in cls)
        raise ValueError(
            f"Invalid TimeWindow value: {value!r}. Must be one of: {allowed}"
        )

    def duration(self) -> timedelta:
        """Return the timedelta span associated with this window."""

        if self is TimeWindow.SHORT_TERM:
            return timedelta(days=7)
        if self is TimeWindow.MEDIUM_TERM:
            return timedelta(days=30)
        return timedelta(days=90)

    def to_time_range(
        self, end_time: datetime | None = None
    ) -> tuple[datetime, datetime]:
        """Compute (start, end) UTC bounds for this window."""

        end = _ensure_utc(end_time or _utcnow())
        start = end - self.duration()
        return start, end


class SentimentContent(BaseModel):
    """Scraped content item (news article, RSS entry, Reddit post, etc.)."""

    model_config = ConfigDict(extra="forbid")

    content_id: str = Field(
        default="",
        description="Stable identifier for the content item (auto-generated).",
    )
    ticker: str = Field(description="Ticker symbol the content primarily targets.")
    source: str | None = Field(
        default=None,
        description="Identifier for the provider/source (e.g., alpha_vantage).",
    )
    title: str = Field(description="Title or descriptive label for the content.")
    summary: str | None = Field(
        default=None, description="Optional short summary or excerpt."
    )
    body: str | None = Field(
        default=None, description="Full text body if available from the source."
    )
    url: HttpUrl | str | None = Field(
        default=None, description="Canonical URL if available."
    )
    published_at: datetime | None = Field(
        default=None, description="Original publication timestamp (UTC)."
    )
    collected_at: datetime | None = Field(
        default=None,
        description="Timestamp when the system ingested the content (UTC).",
    )

    source_url: HttpUrl | None = Field(
        default=None,
        description="URL of the specific content item in the source system.",
    )
    source_type: SourceType | None = Field(
        default=None, description="High-level category of the content source."
    )
    metadata: dict[str, str] | None = Field(
        default=None,
        description="Optional provider-specific attributes (e.g., author, subreddit).",
    )

    @field_validator("ticker")
    @classmethod
    def _normalize_ticker(cls, value: str) -> str:
        """Normalize ticker casing/whitespace."""

        return value.strip().upper()

    @field_validator("published_at", "collected_at")
    @classmethod
    def _ensure_datetime_utc(cls, value: datetime | None) -> datetime | None:
        """Ensure timestamps are timezone-aware UTC."""

        return _ensure_optional_utc(value)

    @model_validator(mode="after")
    def _generate_content_id(self) -> "SentimentContent":
        """Generate stable content_id if not provided.

        Hash is based on: ticker, source, url, and published_at.
        This ensures deduplication across sources.
        """
        if not self.content_id:
            url_str = str(self.url) if self.url else ""
            published_str = self.published_at.isoformat() if self.published_at else ""
            source_str = self.source or "unknown"

            hash_input = f"{self.ticker}:{source_str}:{url_str}:{published_str}"
            self.content_id = f"{source_str}_{abs(hash(hash_input))}"

        return self


class SentimentContentScored(BaseModel):
    """AI-derived scoring metadata tied to a SentimentContent item."""

    model_config = ConfigDict(extra="forbid")

    content: SentimentContent = Field(description="Content payload that was evaluated.")
    sentiment_score: float = Field(
        ge=-1,
        le=1,
        description="Sentiment polarity score where -1 is strongly bearish and +1 strongly bullish.",
    )
    impact_score: float = Field(
        ge=0,
        le=1,
        description="Estimated market impact of the content (0 no impact on trading, +1 maximum impact on stock price).",
    )
    relevance_score: float = Field(
        ge=0,
        le=1,
        description="Degree of relevance of the content to the ticker (0..1).",
    )
    confidence: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Optional confidence metric provided by the scoring agent (0..1).",
    )
    reasoning: str | None = Field(
        default=None,
        description="Free-form rationale from the scoring agent describing how the scores were derived and interpreted.",
    )
    scored_at: datetime = Field(
        default_factory=_utcnow,
        description="Timestamp when the scoring agent generated these values (UTC).",
    )
    model_name: str | None = Field(
        default=None,
        description="Identifier for the LLM / model responsible for the scoring.",
    )

    @field_validator("scored_at")
    @classmethod
    def _ensure_scored_at_utc(cls, value: datetime) -> datetime:
        """Ensure `scored_at` is timezone-aware UTC."""

        return _ensure_utc(value)

    def weight(self) -> float:
        """Compute composite weight for ranking: relevance × impact."""
        return self.relevance_score * self.impact_score


class SentimentAnalysisInput(BaseModel):
    """Input parameters for sentiment analysis processing."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(description="Stock ticker symbol (uppercased).")
    time_window: TimeWindow | None = Field(
        default=None,
        description="Categorical window defining how far back to fetch content (short/medium/long).",
    )
    start_time: datetime | None = Field(
        default=None,
        description="Start timestamp (UTC) for content retrieval and aggregation.",
    )
    end_time: datetime | None = Field(
        default=None,
        description="End timestamp (UTC) for content retrieval and aggregation.",
    )
    limit: int = Field(
        default=50, ge=1, description="Maximum number of scored content items to use."
    )
    min_relevance_score: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Optional minimum relevance filter (0..1).",
    )
    sources: list[str] | None = Field(
        default=None,
        description="Optional allowlist of source identifiers to query (implementation-defined).",
    )
    contents: list[SentimentContentScored] = Field(
        default_factory=list,
        description="Optional pre-scored content items. When provided, fetching/scoring can be skipped.",
    )

    # Optional pre-computed aggregates (to be populated by Aggregator before Agent processing)
    breakdown: SentimentBreakdown | None = Field(
        default=None, description="Pre-computed sentiment breakdown metrics."
    )
    overall_sentiment_score: float | None = Field(
        default=None,
        ge=-1,
        le=1,
        description="Pre-computed weighted average sentiment score.",
    )
    overall_relevance_score: float | None = Field(
        default=None, ge=0, le=1, description="Pre-computed average relevance score."
    )
    overall_impact_score: float | None = Field(
        default=None, ge=0, le=1, description="Pre-computed average impact score."
    )
    top_drivers: list[SentimentContentScored] | None = Field(
        default=None, description="Pre-computed top drivers sorted by weight."
    )

    @field_validator("ticker")
    @classmethod
    def _normalize_ticker(cls, value: str) -> str:
        """Normalize ticker casing/whitespace."""

        return value.strip().upper()

    @field_validator("start_time", "end_time")
    @classmethod
    def _ensure_datetime_utc(cls, value: datetime | None) -> datetime | None:
        """Ensure timestamps are timezone-aware UTC."""

        return _ensure_optional_utc(value)

    @model_validator(mode="after")
    def _validate_time_window(self) -> "SentimentAnalysisInput":
        """Validate that the time window is ordered and non-empty."""

        if self.time_window is not None:
            derived_start, derived_end = self.time_window.to_time_range(self.end_time)
            self.start_time = self.start_time or derived_start
            self.end_time = self.end_time or derived_end

        if self.start_time is None or self.end_time is None:
            raise ValueError(
                "Either time_window or both start_time and end_time must be provided"
            )

        if self.start_time > self.end_time:
            raise ValueError("start_time must be <= end_time")
        return self


class SentimentBreakdown(BaseModel):
    """Counts and percentages for positive/negative/neutral sentiment buckets."""

    model_config = ConfigDict(extra="forbid")

    positive: int = Field(ge=0, description="Count of positively scored items.")
    negative: int = Field(ge=0, description="Count of negatively scored items.")
    neutral: int = Field(ge=0, description="Count of neutral scored items.")
    positive_ratio: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Fraction of items with positive sentiment (0..1).",
    )
    negative_ratio: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Fraction of items with negative sentiment (0..1).",
    )
    neutral_ratio: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description="Fraction of items with neutral sentiment (0..1).",
    )

    @model_validator(mode="after")
    def _compute_missing_ratios(self) -> "SentimentBreakdown":
        """Compute or validate ratios so they sum to 1.0."""

        total = self.positive + self.negative + self.neutral
        if total == 0:
            self.positive_ratio = self.positive_ratio or 0.0
            self.negative_ratio = self.negative_ratio or 0.0
            self.neutral_ratio = self.neutral_ratio or 0.0
            total_ratio = self.positive_ratio + self.negative_ratio + self.neutral_ratio
            if not math.isclose(total_ratio, 0.0, rel_tol=1e-6, abs_tol=1e-6):
                raise ValueError(
                    "Ratios must sum to 0.0 when no content items are present"
                )
            return self
        else:
            self.positive_ratio = (
                self.positive_ratio
                if self.positive_ratio is not None
                else self.positive / total
            )
            self.negative_ratio = (
                self.negative_ratio
                if self.negative_ratio is not None
                else self.negative / total
            )
            self.neutral_ratio = (
                self.neutral_ratio
                if self.neutral_ratio is not None
                else self.neutral / total
            )

        ratios = [self.positive_ratio, self.negative_ratio, self.neutral_ratio]
        if any(value is None for value in ratios):
            raise ValueError(
                "positive_ratio, negative_ratio, and neutral_ratio must be provided or computable"
            )

        total_ratio = sum(ratios)  # type: ignore[arg-type]
        if not math.isclose(total_ratio, 1.0, rel_tol=1e-6, abs_tol=1e-6):
            raise ValueError(
                "positive_ratio + negative_ratio + neutral_ratio must equal 1.0"
            )
        return self


class SentimentReportNarrative(BaseModel):
    """Narrative fields generated by the LLM layer."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(
        description="Natural language summary of the sentiment posture."
    )
    reasoning: str = Field(
        description="Explanation for the summary and scoring decisions."
    )
    highlights: list[str] = Field(
        default_factory=list, description="Key drivers or notable content callouts."
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable monitoring or follow-up suggestions for downstream agents.",
    )


class SentimentReport(BaseModel):
    """Structured sentiment report built from a collection of scored content."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(description="Stock ticker symbol (uppercased).")
    time_window: TimeWindow | None = Field(
        default=None, description="Categorical time window used for aggregation."
    )
    time_period: tuple[datetime, datetime] = Field(
        description="Start/end timestamps (UTC) used to aggregate content."
    )
    generated_at: datetime = Field(description="When the report was generated (UTC).")
    # Categorical fields
    market_trend: MarketTrend = Field(
        description="Overall market sentiment classification for the ticker."
    )
    signal: Signal = Field(
        description="Trade activity signal derived from the aggregated sentiment."
    )

    # Free-form fields
    summary: str = Field(
        description="Natural language summary of the sentiment posture."
    )
    reasoning: str = Field(
        description="Explanation for the summary and scoring decisions."
    )

    highlights: list[str] = Field(
        default_factory=list, description="Merged set of key drivers and risk callouts."
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable next steps or monitoring instructions.",
    )
    # Overall scores
    sentiment_score: float = Field(
        ge=-1,
        le=1,
        description="Aggregate sentiment score for the ticker over the time window (-1..1).",
    )
    relevance_score: float = Field(
        ge=0,
        le=1,
        description="Aggregate relevance score for the ticker over the time window (0..1).",
    )
    impact_score: float = Field(
        ge=0,
        le=1,
        description="Aggregate estimated market impact magnitude over the time window (0..1).",
    )
    breakdown: SentimentBreakdown = Field(
        description="Counts and percentages for positive, negative, and neutral sentiment classifications."
    )

    contents: list[SentimentContentScored] = Field(
        default_factory=list,
        description="Scored content items backing the aggregated sentiment assessment.",
    )
    top_drivers: list[SentimentContentScored] = Field(
        default_factory=list,
        description="Highest weighted content items (ordered by relevance_score * impact_score).",
    )

    @field_validator("ticker")
    @classmethod
    def _normalize_ticker(cls, value: str) -> str:
        """Normalize ticker casing/whitespace."""

        return value.strip().upper()

    @field_validator("generated_at")
    @classmethod
    def _ensure_generated_at_utc(cls, value: datetime) -> datetime:
        """Ensure `generated_at` is timezone-aware UTC."""

        return _ensure_utc(value)

    @field_validator("time_period")
    @classmethod
    def _ensure_time_period_utc(
        cls, value: tuple[datetime, datetime]
    ) -> tuple[datetime, datetime]:
        """Ensure time period boundaries are timezone-aware UTC."""

        start, end = value
        start = _ensure_utc(start)
        end = _ensure_utc(end)
        return start, end

    @model_validator(mode="after")
    def _validate_time_period_order(self) -> "SentimentReport":
        """Validate that the time window is ordered and non-empty."""

        start, end = self.time_period
        if start > end:
            raise ValueError("time_period start must be <= end")
        return self
