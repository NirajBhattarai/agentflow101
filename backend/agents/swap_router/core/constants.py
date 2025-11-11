"""
Constants for Swap Router Agent.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Agent Configuration
AGENT_NAME = "SwapRouterAgent"
AGENT_DESCRIPTION = "Intelligent multi-chain swap routing agent that optimizes large token swaps across chains"
RESPONSE_TYPE = "swap_router"

# Model Configuration
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_USER_ID = "swap_router_user"
DEFAULT_SESSION_ID = "swap_router_session"
ERROR_CANCEL_NOT_SUPPORTED = "Cancel operation not supported"

# Routing Configuration
DEFAULT_MAX_SLIPPAGE_PERCENT = 3.0
DEFAULT_MAX_GAS_SPEND_USD = 500.0
DEFAULT_MIN_LIQUIDITY_USD = 100000.0  # $100K minimum liquidity
DEFAULT_ALLOCATION_STEP = 10000.0  # $10K increments for optimization
DEFAULT_MAX_ITERATIONS = 100

# Supported Chains
SUPPORTED_CHAINS = ["ethereum", "polygon", "hedera"]

# Price Impact Calculation
PRICE_IMPACT_THRESHOLDS = {
    "low": 0.5,      # < 0.5% - excellent
    "medium": 1.5,   # 0.5-1.5% - good
    "high": 3.0,     # 1.5-3% - acceptable
    "very_high": 5.0  # > 3% - warning
}

# Gas Cost Estimates (in USD, approximate)
GAS_COST_ESTIMATES = {
    "ethereum": {
        "swap": 50.0,   # ~$50 for a swap on Ethereum
        "approve": 30.0, # ~$30 for approval
    },
    "polygon": {
        "swap": 0.05,   # ~$0.05 for a swap on Polygon
        "approve": 0.03, # ~$0.03 for approval
    },
    "hedera": {
        "swap": 0.001,  # ~$0.001 for a swap on Hedera
        "approve": 0.001, # ~$0.001 for approval
    },
}

# Execution Time Estimates (seconds)
EXECUTION_TIME_ESTIMATES = {
    "ethereum": 15,   # 15-30 seconds
    "polygon": 120,   # 2-5 minutes
    "hedera": 3,      # ~3 seconds
}


def get_model_name() -> str:
    """Get model name from environment or use default."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def check_api_keys() -> None:
    """Check if API keys are set."""
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY")

