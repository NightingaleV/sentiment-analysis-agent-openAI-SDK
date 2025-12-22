"""Pydantic data models for the sentiment analysis agent."""

from __future__ import annotations

from datetime import datetime, timezone

try:  # Python 3.11+
    from enum import StrEnum
except ImportError:  # pragma: no cover - Python 3.10 fallback for tooling
    from enum import Enum

    class StrEnum(str, Enum):
        """Backport of `enum.StrEnum` for Python < 3.11."""

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


def _utcnow() -> datetime:
    """Return timezone-aware UTC timestamp for default factories."""

    return datetime.now(timezone.utc)


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
        raise ValueError(f"Invalid MarketTrend value: {value!r}. Must be one of: {allowed}")


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
        raise ValueError(f"Invalid SourceType value: {value!r}. Must be one of: {allowed}")


class SentimentContent(BaseModel):
    """Scraped content item (news article, RSS entry, Reddit post, etc.)."""

    model_config = ConfigDict(extra="forbid")

    content_id: str = Field(description="Stable identifier for the content item.")
    ticker: str = Field(description="Ticker symbol the content primarily targets.")
    title: str = Field(description="Title or descriptive label for the content.")
    summary: str | None = Field(default=None, description="Optional short summary or excerpt.")
    body: str | None = Field(default=None, description="Full text body if available from the source.")
    url: HttpUrl | None = Field(default=None, description="Canonical URL if available.")
    published_at: datetime | None = Field(default=None, description="Original publication timestamp (UTC).")
    collected_at: datetime | None = Field(default=None, description="Timestamp when the system ingested the content (UTC).")

    source_url: HttpUrl | None = Field(
        default=None,
        description="URL of the specific content item in the source system.",
    )
    source_type: SourceType | None = Field(default=None,description="High-level category of the content source.")
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

        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class SentimentContentScore(BaseModel):
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
    model_name: str | None = Field(default=None,description="Identifier for the LLM / model responsible for the scoring.",
    )

    @field_validator("scored_at")
    @classmethod
    def _ensure_scored_at_utc(cls, value: datetime) -> datetime:
        """Ensure `scored_at` is timezone-aware UTC."""

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class SentimentReport(BaseModel):
    """Structured sentiment report built from a collection of scored content."""

    model_config = ConfigDict(extra="forbid")

    ticker: str = Field(description="Stock ticker symbol (uppercased).")
    time_period: tuple[datetime, datetime] = Field(
        description="Start/end timestamps (UTC) used to aggregate content.",
    )
    generated_at: datetime = Field(description="When the report was generated (UTC).")
    # Categorical fields
    market_trend: MarketTrend = Field(description="Overall market sentiment classification for the ticker.")
    signal: Signal = Field(description="Trade activity signal derived from the aggregated sentiment.")
    
    # Free-form fields
    summary: str = Field(description="Natural language summary of the sentiment posture.")
    reasoning: str = Field(description="Explanation for the summary and scoring decisions.")
    
    highlights: list[str] = Field(
        default_factory=list,
        description="Merged set of key drivers and risk callouts.",
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
        ge=-1,
        le=1,
        description="Estimated net impact of sentiment on the ticker and price movement (0..1).",
    )

    contents: list[SentimentContentScore] | None = Field(
        default_factory=list,
        description="Scored content items backing the aggregated sentiment assessment.",
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

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @field_validator("time_period")
    @classmethod
    def _ensure_time_period_utc(cls, value: tuple[datetime, datetime]) -> tuple[datetime, datetime]:
        """Ensure time period boundaries are timezone-aware UTC."""

        start, end = value
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        else:
            start = start.astimezone(timezone.utc)

        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        else:
            end = end.astimezone(timezone.utc)

        return start, end

    @model_validator(mode="after")
    def _validate_time_period_order(self) -> "SentimentReport":
        """Validate that the time window is ordered and non-empty."""

        start, end = self.time_period
        if start > end:
            raise ValueError("time_period start must be <= end")
        return self
