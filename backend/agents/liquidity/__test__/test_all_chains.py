"""
Unit tests for all chains liquidity tool.
Tests the aggregation of liquidity across all chains.
"""

from agents.liquidity.tools.all_chains import get_liquidity_all_chains
from lib.shared.blockchain.liquidity.constants import (
    POLYGON_TOKENS,
    HEDERA_TOKENS,
)


class TestAllChainsLiquidity:
    """Test cases for all chains liquidity aggregation."""

    def test_all_chains_response_structure(self):
        """Test that all chains response has correct structure."""
        result = get_liquidity_all_chains("USDC")
        assert result["type"] == "liquidity_summary"
        assert "token_address" in result
        assert "chains" in result
        assert "total_tvl" in result
        assert "total_volume_24h" in result

    def test_all_chains_includes_all_networks(self):
        """Test that all supported chains are included."""
        result = get_liquidity_all_chains("USDC")
        chains = result["chains"]
        assert "polygon" in chains
        assert "hedera" in chains

    def test_all_chains_token_addresses(self):
        """Test that token addresses are correctly resolved for each chain."""
        result = get_liquidity_all_chains("USDC")
        chains = result["chains"]

        assert chains["polygon"]["token_address"] == POLYGON_TOKENS["USDC"]
        assert chains["hedera"]["token_address"] == HEDERA_TOKENS["USDC"]

    def test_all_chains_pools_exist(self):
        """Test that each chain has pools data."""
        result = get_liquidity_all_chains("USDC")
        chains = result["chains"]

        for chain_name, chain_data in chains.items():
            assert "pools" in chain_data, f"{chain_name} missing pools"
            assert len(chain_data["pools"]) > 0, f"{chain_name} has no pools"

    def test_all_chains_totals(self):
        """Test that totals are calculated and present."""
        result = get_liquidity_all_chains("USDC")
        assert result["total_tvl"] is not None
        assert result["total_volume_24h"] is not None
        # Totals should be strings with dollar signs
        assert isinstance(result["total_tvl"], str)
        assert isinstance(result["total_volume_24h"], str)
