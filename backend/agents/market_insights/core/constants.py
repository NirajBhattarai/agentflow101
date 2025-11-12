"""
Constants for Market Insights Agent.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Default values
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_USER_ID = "market_insights_user"
DEFAULT_SESSION_ID = "market_insights_session"
DEFAULT_APP_NAME = "agents"

# Agent configuration
AGENT_NAME = "MarketInsightsAgent"
AGENT_DESCRIPTION = "Fetches liquidity across pools, volume, trending token addresses, and real-time prices using CoinGecko API"

# Response type
RESPONSE_TYPE = "market_insights"

# CoinGecko API Configuration
# Default to Demo API (api.coingecko.com)
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_ONCHAIN_API_BASE = "https://api.coingecko.com/api/v3/onchain"

# Supported networks (GeckoTerminal network IDs)
NETWORK_ETH = "eth"
NETWORK_POLYGON = "polygon"
NETWORK_HEDERA = "hedera"
SUPPORTED_NETWORKS = [NETWORK_ETH, NETWORK_POLYGON, NETWORK_HEDERA]

# Error messages
ERROR_API_KEY_MISSING = (
    "CoinGecko API key not found. Set COINGECKO_API_KEY environment variable."
)
ERROR_NETWORK_NOT_SUPPORTED = (
    "Network not supported. Supported networks: eth, polygon, hedera"
)
ERROR_TOKEN_ADDRESS_MISSING = "Token address is required"
ERROR_POOL_ADDRESS_MISSING = "Pool address is required"
ERROR_EMPTY_RESPONSE = "Empty response from agent"
ERROR_INVALID_JSON = "Invalid JSON response"
ERROR_EXECUTION_ERROR = "Execution error"
ERROR_CANCEL_NOT_SUPPORTED = "cancel not supported"
ERROR_VALIDATION_FAILED = "Validation failed"


def get_model_name() -> str:
    """Get Gemini model name from environment."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def get_coingecko_api_key() -> str:
    """Get CoinGecko API key from environment."""
    api_key = os.getenv("COINGECKO_API_KEY")
    if not api_key:
        print(f"⚠️  Warning: {ERROR_API_KEY_MISSING}")
    return api_key or ""


def get_coingecko_api_base() -> str:
    """Get the CoinGecko API base URL (Demo API)."""
    return COINGECKO_API_BASE


def get_coingecko_onchain_api_base() -> str:
    """Get the CoinGecko Onchain API base URL (Demo API)."""
    return COINGECKO_ONCHAIN_API_BASE


def get_coingecko_api_header_name() -> str:
    """Get the CoinGecko API header name (Demo API)."""
    return "x-cg-demo-api-key"


def get_coingecko_api_param_name() -> str:
    """Get the CoinGecko API parameter name (Demo API)."""
    return "x_cg_demo_api_key"


def check_api_keys() -> None:
    """Check if API keys are configured."""
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY")
    if not os.getenv("COINGECKO_API_KEY"):
        print(f"⚠️  Warning: {ERROR_API_KEY_MISSING}")
