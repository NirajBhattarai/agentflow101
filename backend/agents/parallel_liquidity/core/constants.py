"""
Constants for Parallel Liquidity Agent.

Contains configuration values, default values, and response templates.
"""

import os

# Default values
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_USER_ID = "remote_agent"
DEFAULT_SESSION_ID = "default_session"
DEFAULT_APP_NAME = "agents"

# Agent configuration
AGENT_NAME = "ParallelLiquidityAgent"
AGENT_DESCRIPTION = "Fetches liquidity from Hedera and Polygon chains in parallel"

# Response type
RESPONSE_TYPE = "parallel_liquidity"

# Chain names
CHAIN_HEDERA = "hedera"
CHAIN_POLYGON = "polygon"

# Default fees (basis points)
DEFAULT_HEDERA_FEE_BPS = 30
DEFAULT_POLYGON_FEE_BPS = 25

# Error messages
ERROR_TOKEN_PAIR_NOT_FOUND = (
    "Could not extract token pair from query. "
    "Please provide format like 'ETH/USDT' or 'HBAR/USDC'"
)
ERROR_EMPTY_RESPONSE = "Empty response from agent"
ERROR_INVALID_JSON = "Invalid JSON response"
ERROR_EXECUTION_ERROR = "Execution error"
ERROR_CANCEL_NOT_SUPPORTED = "cancel not supported"
ERROR_VALIDATION_FAILED = "Validation failed"
ERROR_RESULT_COMBINATION_FAILED = "Failed to combine results from chains"

# Sequential fallback instruction
SEQUENTIAL_FALLBACK_INSTRUCTION = """
You are a liquidity query agent. When given a token pair like "ETH/USDT",
fetch liquidity from both Hedera and Polygon chains.
Use get_liquidity_hedera for Hedera and get_liquidity_polygon for Polygon.
Return combined results in JSON format.
"""

# Output keys for sub-agents
OUTPUT_KEY_HEDERA = "hedera_liquidity"
OUTPUT_KEY_POLYGON = "polygon_liquidity"


def get_model_name() -> str:
    """Get Gemini model name from environment."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def check_api_keys() -> None:
    """Check if API keys are configured."""
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY")
