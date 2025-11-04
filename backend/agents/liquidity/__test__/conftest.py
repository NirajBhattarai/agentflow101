"""
Pytest configuration and fixtures for liquidity agent tests.
"""
import pytest
import os
from typing import Dict


@pytest.fixture
def rpc_urls() -> Dict[str, str]:
    """RPC URLs for different chains."""
    return {
        "ethereum": os.getenv(
            "ETHEREUM_RPC_URL",
            "https://eth.llamarpc.com"  # Public RPC
        ),
        "bsc": os.getenv(
            "BSC_RPC_URL",
            "https://bsc-dataseed1.binance.org"  # Public BSC RPC
        ),
        "polygon": os.getenv(
            "POLYGON_RPC_URL",
            "https://polygon.llamarpc.com"  # Public Polygon RPC
        ),
        "hedera": os.getenv(
            "HEDERA_RPC_URL",
            "https://mainnet.hashio.io/api"  # Public Hedera RPC
        ),
    }


@pytest.fixture
def test_token_addresses() -> Dict[str, Dict[str, str]]:
    """Test token addresses for each chain."""
    return {
        "ethereum": {
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        },
        "bsc": {
            "USDC": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
            "USDT": "0x55d398326f99059fF775485246999027B3197955",
        },
        "polygon": {
            "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        },
        "hedera": {
            "USDC": "0.0.456858",
            "HBAR": "0.0.0",
        },
    }


@pytest.fixture
def test_pool_addresses() -> Dict[str, Dict[str, str]]:
    """Test pool addresses for each chain."""
    return {
        "ethereum": {
            "USDC-ETH_UNISWAP_V3": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8",
            "USDC-USDT_UNISWAP_V3": "0x3416cF6C708Da44DB2624D63ea0AAef7113527C6",
        },
        "bsc": {
            "USDT-BNB_PANCAKESWAP_V3": "0x133B3d95bAD5405d14d53473671200e5C8e3E112",
        },
        "polygon": {
            "USDC-MATIC_QUICKSWAP": "0x6e7a5FAFcec6BB1e78bAE2A1F0B6121BF5779D35",
        },
    }

