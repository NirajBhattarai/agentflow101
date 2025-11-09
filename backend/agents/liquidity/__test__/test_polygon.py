"""
Unit tests for Polygon liquidity tool.
Tests fetch actual data from Polygon chain using RPC.
"""

from web3 import Web3
from agents.liquidity.tools.polygon import get_liquidity_polygon
from agents.liquidity.tools.constants import POLYGON_TOKENS, POLYGON_POOLS


class TestPolygonLiquidity:
    """Test cases for Polygon liquidity fetching."""

    def test_token_address_lookup(self):
        """Test that token symbols are resolved to addresses."""
        result = get_liquidity_polygon("USDC")
        assert result["token_address"] == POLYGON_TOKENS["USDC"]
        assert result["chain"] == "polygon"
        assert "pools" in result

    def test_with_address_directly(self):
        """Test with direct token address."""
        token_addr = POLYGON_TOKENS["USDT"]
        result = get_liquidity_polygon(token_addr)
        assert result["token_address"] == token_addr
        assert result["chain"] == "polygon"

    def test_with_pool_address(self):
        """Test with specific pool address."""
        pool_addr = POLYGON_POOLS["USDC-MATIC"]["quickswap"]
        result = get_liquidity_polygon("USDC", pool_address=pool_addr)
        assert result["chain"] == "polygon"
        assert len(result["pools"]) > 0
        assert result["pools"][0]["pool_address"] == pool_addr

    def test_pools_from_constants(self):
        """Test that pools are fetched from constants."""
        result = get_liquidity_polygon("USDC")
        assert len(result["pools"]) > 0
        assert all("pool_address" in pool for pool in result["pools"])
        assert all("dex" in pool for pool in result["pools"])

    def test_polygon_rpc_connection(self, rpc_urls):
        """Test connection to Polygon RPC endpoint."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["polygon"]))
        assert w3.is_connected(), "Failed to connect to Polygon RPC"

    def test_polygon_token_contract_exists(self, rpc_urls, test_token_addresses):
        """Test that token contract exists on Polygon chain."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["polygon"]))
        usdc_address = test_token_addresses["polygon"]["USDC"]

        # Check if contract exists (has code)
        code = w3.eth.get_code(usdc_address)
        assert len(code) > 0, f"Contract at {usdc_address} does not exist or has no code"

    def test_polygon_pool_contract_exists(self, rpc_urls, test_pool_addresses):
        """Test that pool contract exists on Polygon chain."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["polygon"]))
        pool_address = test_pool_addresses["polygon"]["USDC-MATIC_QUICKSWAP"]

        # Check if pool contract exists
        code = w3.eth.get_code(pool_address)
        assert len(code) > 0, f"Pool contract at {pool_address} does not exist"

    def test_polygon_get_latest_block(self, rpc_urls):
        """Test fetching latest block from Polygon."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["polygon"]))
        latest_block = w3.eth.block_number
        assert latest_block > 0, "Failed to get latest block number"
        assert isinstance(latest_block, int)

    def test_polygon_chain_id(self, rpc_urls):
        """Test that Polygon chain ID is correct (137 for mainnet)."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["polygon"]))
        chain_id = w3.eth.chain_id
        assert chain_id == 137, f"Expected chain ID 137 for Polygon mainnet, got {chain_id}"
