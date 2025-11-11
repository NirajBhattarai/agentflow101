"""
Constants for Swap Agent.

Configuration values, defaults, and constants.
"""

import os

# Default values
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_USER_ID = "remote_agent"
DEFAULT_SESSION_ID = "default_session"
DEFAULT_CHAIN = "hedera"
DEFAULT_TOKEN_IN = "HBAR"
DEFAULT_TOKEN_OUT = "USDC"
DEFAULT_AMOUNT = "0.01"
DEFAULT_SLIPPAGE = 0.5
DEFAULT_CONFIRMATION_THRESHOLD = 100.0

# Agent configuration
AGENT_NAME = "swap_agent"
AGENT_DESCRIPTION = "An agent that handles token swaps on blockchain chains including Polygon and Hedera"
RESPONSE_TYPE = "swap"

# Error messages
ERROR_VALIDATION_FAILED = "Validation failed"
ERROR_EXECUTION_ERROR = "Execution error"
ERROR_EMPTY_RESPONSE = "Empty response from agent"
ERROR_INVALID_JSON = "Invalid JSON response"
ERROR_CANCEL_NOT_SUPPORTED = "cancel not supported"
ERROR_CHAIN_NOT_SPECIFIED = "Chain not specified in query"
ERROR_TOKEN_IN_NOT_FOUND = "Could not determine which token to swap from"
ERROR_TOKEN_OUT_NOT_FOUND = "Could not determine which token to swap to"

# Chains
CHAIN_HEDERA = "hedera"
CHAIN_POLYGON = "polygon"
CHAIN_UNKNOWN = "unknown"


# Model configuration
def get_model_name() -> str:
    """Get Gemini model name from environment."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def check_api_keys() -> None:
    """Check if API keys are configured."""
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY")
