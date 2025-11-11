"""
Constants for Multi-Chain Liquidity Agent.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Default values
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_USER_ID = "multichain_liquidity_user"
DEFAULT_SESSION_ID = "multichain_liquidity_session"
DEFAULT_APP_NAME = "agents"

# Agent configuration
AGENT_NAME = "MultiChainLiquidityAgent"
AGENT_DESCRIPTION = (
    "Fetches liquidity from Hedera, Polygon, and Ethereum chains sequentially"
)

# Response type
RESPONSE_TYPE = "multichain_liquidity"

# Chain names
CHAIN_HEDERA = "hedera"
CHAIN_POLYGON = "polygon"
CHAIN_ETHEREUM = "ethereum"

# Default fees (basis points)
DEFAULT_HEDERA_FEE_BPS = 30
DEFAULT_POLYGON_FEE_BPS = 25
DEFAULT_ETHEREUM_FEE_BPS = 30

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

# Output keys
OUTPUT_KEY_HEDERA = "hedera_liquidity"
OUTPUT_KEY_POLYGON = "polygon_liquidity"
OUTPUT_KEY_ETHEREUM = "ethereum_liquidity"


def get_model_name() -> str:
    """Get Gemini model name from environment."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def check_api_keys() -> None:
    """Check if API keys are configured."""
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY")
