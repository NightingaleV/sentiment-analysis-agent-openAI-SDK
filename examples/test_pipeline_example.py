"""Quick integration test for the sentiment scoring pipeline.

This script tests the pipeline with a real HuggingFace model to ensure
everything works end-to-end.
"""

import asyncio
from datetime import datetime, timedelta, timezone

from sentiment_analysis_agent.models.sentiment_analysis_models import SentimentContent
from sentiment_analysis_agent.pipeline import ScoringConfig, SentimentScoringPipeline


async def main():
    """Run integration test."""
    print("🚀 Starting sentiment scoring pipeline integration test...")
    print()

    # Create test content
    positive_content = SentimentContent(
        ticker="AAPL",
        title="Apple reports record-breaking quarterly earnings",
        summary="Apple Inc. announced its strongest quarter ever with revenue exceeding analyst expectations.",
        body="Apple Inc. (AAPL) has announced record-breaking quarterly earnings for Q4 2024, "
        "beating Wall Street expectations. The company reported revenue of $123.5 billion, "
        "driven by strong iPhone 15 sales and growing services revenue. CEO Tim Cook stated "
        "that the results demonstrate continued innovation and customer loyalty.",
        published_at=datetime.now(timezone.utc) - timedelta(hours=2),
        source="test_integration",
    )
    negative_content = SentimentContent(
        ticker="TSLA",
        title="Tesla issues profit warning amid production setbacks",
        summary="Tesla expects margins to compress significantly due to persistent supply chain issues.",
        body="Tesla Inc. (TSLA) warned investors that a combination of parts shortages, quality rework, and shipping "
        "bottlenecks will pressure profitability and delay expansion plans in the next quarter.",
        published_at=datetime.now(timezone.utc) - timedelta(hours=5),
        source="test_integration",
    )
    slightly_negative_content = SentimentContent(
        ticker="MSFT",
        title="Microsoft moderates guidance amid cloud optimization pause",
        summary="Microsoft anticipates a brief lull in Azure growth as clients optimize existing workloads.",
        body="Microsoft Corp. (MSFT) forecast modestly softer cloud revenue for the upcoming quarter, emphasizing that "
        "optimization programs are cyclical and long-term demand remains intact.",
        published_at=datetime.now(timezone.utc) - timedelta(days=1),
        source="test_integration",
    )
    slightly_positive_content = SentimentContent(
        ticker="GOOGL",
        title="Alphabet extends AI tools to telecom ecosystem",
        summary="Alphabet deepens collaborations to embed Vertex AI services with regional network partners.",
        body="Alphabet Inc. (GOOGL) announced incremental partnerships with Asia-Pacific telecom operators to "
        "integrate Vertex AI tools, signalling steady adoption with moderate near-term revenue contributions.",
        published_at=datetime.now(timezone.utc) - timedelta(hours=8),
        source="test_integration",
    )

    print(f"📰 Strong Positive Content:")
    print(f"   Ticker: {positive_content.ticker}")
    print(f"   Title: {positive_content.title}")
    print()
    print(f"⚠️ Strong Negative Content:")
    print(f"   Ticker: {negative_content.ticker}")
    print(f"   Title: {negative_content.title}")
    print()
    print(f"🔻 Slightly Negative Content:")
    print(f"   Ticker: {slightly_negative_content.ticker}")
    print(f"   Title: {slightly_negative_content.title}")
    print()
    print(f"🔺 Slightly Positive Content:")
    print(f"   Ticker: {slightly_positive_content.ticker}")
    print(f"   Title: {slightly_positive_content.title}")
    print()

    # Create pipeline with default config
    print("🔧 Initializing pipeline...")
    from sentiment_analysis_agent.pipeline.config import ModelType
    config = ScoringConfig(model_type=ModelType.DISTILROBERTA_FINETUNED)
    pipeline = SentimentScoringPipeline(config)
    print(f"   Model: {config.model_type.value}")
    print(f"   Device: {pipeline._model_strategy.device.value}")
    print()

    # Score the content
    print("⚡ Scoring positive content (this may take a moment on first run)...")
    positive_scored = await pipeline.score(positive_content)
    print()
    print("⚡ Scoring strong negative content...")
    negative_scored = await pipeline.score(negative_content)
    print()
    print("⚡ Scoring slightly negative content...")
    slightly_negative_scored = await pipeline.score(slightly_negative_content)
    print()
    print("⚡ Scoring slightly positive content...")
    slightly_positive_scored = await pipeline.score(slightly_positive_content)
    print()

    # Display results
    print("✅ Scoring Complete!")
    print()
    print(f"📊 Strong Positive Results:")
    print(f"   Sentiment Score: {positive_scored.sentiment_score:.2f} (-1 to 1)")
    print(f"   Relevance Score: {positive_scored.relevance_score:.2f} (0 to 1)")
    print(f"   Impact Score: {positive_scored.impact_score:.2f} (0 to 1)")
    print(f"   Confidence: {positive_scored.confidence:.2f} (0 to 1)")
    print(f"   Model: {positive_scored.model_name}")
    print()
    print(f"📉 Strong Negative Results:")
    print(f"   Sentiment Score: {negative_scored.sentiment_score:.2f} (-1 to 1)")
    print(f"   Relevance Score: {negative_scored.relevance_score:.2f} (0 to 1)")
    print(f"   Impact Score: {negative_scored.impact_score:.2f} (0 to 1)")
    print(f"   Confidence: {negative_scored.confidence:.2f} (0 to 1)")
    print(f"   Model: {negative_scored.model_name}")
    print()
    print(f"📉 Slightly Negative Results:")
    print(
        f"   Sentiment Score: {slightly_negative_scored.sentiment_score:.2f} (-1 to 1)"
    )
    print(
        f"   Relevance Score: {slightly_negative_scored.relevance_score:.2f} (0 to 1)"
    )
    print(f"   Impact Score: {slightly_negative_scored.impact_score:.2f} (0 to 1)")
    print(f"   Confidence: {slightly_negative_scored.confidence:.2f} (0 to 1)")
    print(f"   Model: {slightly_negative_scored.model_name}")
    print()
    print(f"📈 Slightly Positive Results:")
    print(
        f"   Sentiment Score: {slightly_positive_scored.sentiment_score:.2f} (-1 to 1)"
    )
    print(
        f"   Relevance Score: {slightly_positive_scored.relevance_score:.2f} (0 to 1)"
    )
    print(f"   Impact Score: {slightly_positive_scored.impact_score:.2f} (0 to 1)")
    print(f"   Confidence: {slightly_positive_scored.confidence:.2f} (0 to 1)")
    print(f"   Model: {slightly_positive_scored.model_name}")
    print()
    print(f"💡 Strong Positive Reasoning:")
    print(f"   {positive_scored.reasoning}")
    print()
    print(f"💡 Strong Negative Reasoning:")
    print(f"   {negative_scored.reasoning}")
    print()
    print(f"💡 Slightly Negative Reasoning:")
    print(f"   {slightly_negative_scored.reasoning}")
    print()
    print(f"💡 Slightly Positive Reasoning:")
    print(f"   {slightly_positive_scored.reasoning}")
    print()

    # Test batch scoring
    print("🔄 Testing batch scoring with multiple items...")
    batch_contents = [
        positive_content,
        negative_content,
        slightly_negative_content,
        slightly_positive_content,
    ]

    scored_batch = await pipeline.score_batch(batch_contents)
    print(f"   Processed {len(scored_batch)} items successfully")
    for i, scored_item in enumerate(scored_batch, 1):
        print(
            f"   Item {i}: {scored_item.content.ticker} -> Sentiment: {scored_item.sentiment_score:.2f}"
        )
    print()

    print("🎉 Integration test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
