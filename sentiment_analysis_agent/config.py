"""Configuration settings for sentiment analysis agent."""

import os


def _str_to_bool(value: str) -> bool:
    """Convert string to boolean."""
    return value.lower() in ("true", "1", "yes", "on")


# Mock data toggle - defaults to True if not specified
USE_MOCKS = _str_to_bool(os.getenv("USE_MOCKS", "true"))
USE_LLM_MOCKS = _str_to_bool(os.getenv("USE_LLM_MOCKS", "true"))

# API Keys
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", None)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)

# Model selection
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
