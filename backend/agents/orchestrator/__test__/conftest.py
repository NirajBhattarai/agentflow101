"""
Pytest configuration and fixtures for orchestrator agent tests.
"""

import pytest


@pytest.fixture
def test_queries() -> dict:
    """Test queries for orchestrator."""
    return {
        "balance": "Get my balance on Polygon",
        "liquidity": "Show me liquidity for HBAR/USDC",
        "swap": "Swap 0.1 HBAR to USDC on Hedera",
        "bridge": "Bridge 100 USDC from Hedera to Polygon",
    }
