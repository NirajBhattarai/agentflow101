"""
Pytest configuration and fixtures for parallel liquidity agent tests.
"""

import pytest
import os
from typing import Dict


@pytest.fixture
def rpc_urls() -> Dict[str, str]:
    """RPC URLs for different chains."""
    return {
        "polygon": os.getenv(
            "POLYGON_RPC_URL",
            "https://polygon.llamarpc.com",
        ),
        "hedera": os.getenv(
            "HEDERA_RPC_URL",
            "https://mainnet.hashio.io/api",
        ),
    }


@pytest.fixture
def test_token_pairs() -> list:
    """Test token pairs for liquidity queries."""
    return [
        "HBAR/USDC",
        "ETH/USDT",
        "MATIC/USDC",
        "USDC/USDT",
    ]


@pytest.fixture
def mock_hedera_liquidity_result() -> dict:
    """Mock Hedera liquidity result."""
    return {
        "chain": "hedera",
        "pools": [
            {
                "pool_address": "0x1234567890abcdef",
                "dex": "SaucerSwap",
                "tvl": "$1000000",
                "liquidity": "2000000",
            }
        ],
    }


@pytest.fixture
def mock_polygon_liquidity_result() -> dict:
    """Mock Polygon liquidity result."""
    return {
        "chain": "polygon",
        "pools": [
            {
                "pool_address": "0xabcdef1234567890",
                "dex": "QuickSwap",
                "tvl": "$500000",
                "liquidity": "1000000",
            }
        ],
    }
