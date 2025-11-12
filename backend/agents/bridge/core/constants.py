"""
Constants for Bridge Agent.

Configuration values, defaults, and constants.
"""

import os

# Default values
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_USER_ID = "remote_agent"
DEFAULT_SESSION_ID = "default_session"
DEFAULT_SOURCE_CHAIN = "hedera"
DEFAULT_DESTINATION_CHAIN = "polygon"
DEFAULT_TOKEN = "USDC"
DEFAULT_AMOUNT = "100.0"
DEFAULT_CONFIRMATION_THRESHOLD = 1000.0

# Agent configuration
AGENT_NAME = "bridge_agent"
AGENT_DESCRIPTION = "An agent that handles token bridging between blockchain chains including Hedera and Polygon using EtaBridge"
RESPONSE_TYPE = "bridge"

# Error messages
ERROR_VALIDATION_FAILED = "Validation failed"
ERROR_EXECUTION_ERROR = "Execution error"
ERROR_EMPTY_RESPONSE = "Empty response from agent"
ERROR_INVALID_JSON = "Invalid JSON response"
ERROR_CANCEL_NOT_SUPPORTED = "cancel not supported"
ERROR_CHAIN_NOT_SPECIFIED = "Chain not specified in query"
ERROR_TOKEN_NOT_FOUND = "Could not determine which token to bridge"
ERROR_INVALID_BRIDGE_PAIR = "Invalid bridge pair - only Hedera <-> Polygon supported"

# Chains
CHAIN_HEDERA = "hedera"
CHAIN_POLYGON = "polygon"
CHAIN_UNKNOWN = "unknown"

# EtaBridge configuration
ETABRIDGE_API_BASE_URL = os.getenv("ETABRIDGE_API_BASE_URL", "https://api.etaswap.com/bridge")
ETABRIDGE_SUPPORTED_CHAINS = [CHAIN_HEDERA, CHAIN_POLYGON]
# EtaBridge only supports USDC for bridging
ETABRIDGE_SUPPORTED_TOKENS = ["USDC"]

# EtaBridge contract address on Hedera
ETABRIDGE_CONTRACT_ADDRESS = "0xdc038e291d83e218c7bdf549059412ed7ed9133e"

# Chain IDs for EtaBridge (LayerZero endpoint IDs)
# Note: EtaBridge uses LayerZero for cross-chain messaging, so we use LayerZero chain IDs
ETABRIDGE_CHAIN_IDS = {
    CHAIN_HEDERA: 296,  # Hedera mainnet LayerZero endpoint ID
    CHAIN_POLYGON: 30106,  # Polygon LayerZero endpoint ID (different from native Polygon chain ID)
}


# Model configuration
def get_model_name() -> str:
    """Get Gemini model name from environment."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def check_api_keys() -> None:
    """Check if API keys are configured."""
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY")

