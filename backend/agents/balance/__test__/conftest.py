"""
Pytest configuration and fixtures for balance agent tests.
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
            "https://polygon.llamarpc.com",  # Public Polygon RPC
        ),
        "hedera": os.getenv(
            "HEDERA_RPC_URL",
            "https://mainnet-public.mirrornode.hedera.com",  # Public Hedera Mirror Node
        ),
    }


@pytest.fixture
def test_account_addresses() -> Dict[str, str]:
    """Test account addresses for each chain."""
    return {
        "polygon": os.getenv(
            "TEST_POLYGON_ACCOUNT",
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik's address (public)
        ),
        "hedera": os.getenv(
            "TEST_HEDERA_ACCOUNT",
            "0.0.2",  # Public Hedera account (treasury)
        ),
    }


@pytest.fixture
def test_token_addresses() -> Dict[str, Dict[str, str]]:
    """Test token addresses for each chain."""
    return {
        "polygon": {
            "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        },
        "hedera": {
            "USDC": "0.0.456858",
            "HBAR": "0.0.0",
        },
    }
