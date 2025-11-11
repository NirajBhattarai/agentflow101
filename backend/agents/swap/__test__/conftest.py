"""
Pytest configuration and fixtures for swap agent tests.
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
            "https://polygon-rpc.com",
        ),
        "hedera": os.getenv(
            "HEDERA_RPC_URL",
            "https://mainnet-public.mirrornode.hedera.com",
        ),
    }


@pytest.fixture
def test_account_addresses() -> Dict[str, str]:
    """Test account addresses for each chain."""
    return {
        "polygon": os.getenv(
            "TEST_POLYGON_ACCOUNT",
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        ),
        "hedera": os.getenv(
            "TEST_HEDERA_ACCOUNT",
            "0.0.2",
        ),
    }


@pytest.fixture
def test_swap_params() -> Dict[str, Dict]:
    """Test swap parameters for different scenarios."""
    return {
        "hedera_hbar_usdc": {
            "chain": "hedera",
            "token_in_symbol": "HBAR",
            "token_out_symbol": "USDC",
            "amount_in": "0.01",
            "account_address": "0.0.2",
            "slippage_tolerance": 0.5,
        },
        "polygon_matic_usdc": {
            "chain": "polygon",
            "token_in_symbol": "MATIC",
            "token_out_symbol": "USDC",
            "amount_in": "0.1",
            "account_address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            "slippage_tolerance": 0.5,
        },
    }
