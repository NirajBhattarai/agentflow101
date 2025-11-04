"""
Unit tests for Hedera liquidity tool.
Tests fetch actual data from Hedera chain using RPC.
"""

import pytest
import requests
from agents.liquidity.tools.hedera import get_liquidity_hedera
from agents.liquidity.tools.constants import HEDERA_TOKENS, HEDERA_POOLS


class TestHederaLiquidity:
    """Test cases for Hedera liquidity fetching."""

    def test_token_address_lookup(self):
        """Test that token symbols are resolved to addresses."""
        result = get_liquidity_hedera("USDC")
        assert result["token_address"] == HEDERA_TOKENS["USDC"]
        assert result["chain"] == "hedera"
        assert "pools" in result

    def test_with_address_directly(self):
        """Test with direct token address."""
        token_addr = HEDERA_TOKENS["USDC"]
        result = get_liquidity_hedera(token_addr)
        assert result["token_address"] == token_addr
        assert result["chain"] == "hedera"

    def test_with_pool_address(self):
        """Test with specific pool address."""
        pool_addr = HEDERA_POOLS["USDC-HBAR"]["saucerswap"]
        result = get_liquidity_hedera("USDC", pool_address=pool_addr)
        assert result["chain"] == "hedera"
        assert len(result["pools"]) > 0
        assert result["pools"][0]["pool_address"] == pool_addr

    def test_pools_from_constants(self):
        """Test that pools are fetched from constants."""
        result = get_liquidity_hedera("USDC")
        assert len(result["pools"]) > 0
        assert all("pool_address" in pool for pool in result["pools"])
        assert all("dex" in pool for pool in result["pools"])

    def test_hedera_rpc_connection(self, rpc_urls):
        """Test connection to Hedera RPC endpoint."""
        # Hedera uses REST API, not standard Web3 RPC
        try:
            response = requests.get(f"{rpc_urls['hedera']}/status", timeout=5)
            assert response.status_code == 200, "Failed to connect to Hedera API"
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Could not connect to Hedera API: {e}")

    def test_hedera_api_endpoint(self, rpc_urls):
        """Test that Hedera API endpoint is accessible."""
        try:
            # Test basic connectivity
            response = requests.get(rpc_urls["hedera"], timeout=5)
            # Hedera API might return different status codes
            assert response.status_code in [200, 404, 405], (
                f"Unexpected status code: {response.status_code}"
            )
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Could not connect to Hedera API: {e}")
