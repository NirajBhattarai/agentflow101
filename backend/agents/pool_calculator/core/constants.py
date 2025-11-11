"""
Constants for Pool Calculator Agent.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Agent Configuration
AGENT_NAME = "PoolCalculatorAgent"
AGENT_DESCRIPTION = "Agent that processes liquidity and slot0 data to perform calculations and provide insights using LLM"

# Model Configuration
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_USER_ID = "pool_calculator_user"
DEFAULT_SESSION_ID = "pool_calculator_session"

# Response Type
RESPONSE_TYPE = "pool_calculation"


def get_model_name() -> str:
    """Get model name from environment or use default."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def check_api_keys() -> None:
    """Check if API keys are set."""
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY")

