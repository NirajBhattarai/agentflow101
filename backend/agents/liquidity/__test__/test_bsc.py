"""
Unit tests for BSC (Binance Smart Chain) liquidity tool.
Tests fetch actual data from BSC chain using RPC.
"""
import pytest
from web3 import Web3
from agents.liquidity.tools.bsc import get_liquidity_bsc
from agents.liquidity.tools.constants import BSC_TOKENS, BSC_POOLS


class TestBSCLiquidity:
    """Test cases for BSC liquidity fetching."""
    
    def test_token_address_lookup(self):
        """Test that token symbols are resolved to addresses."""
        result = get_liquidity_bsc("USDC")
        assert result["token_address"] == BSC_TOKENS["USDC"]
        assert result["chain"] == "bsc"
        assert "pools" in result
    
    def test_with_address_directly(self):
        """Test with direct token address."""
        token_addr = BSC_TOKENS["USDT"]
        result = get_liquidity_bsc(token_addr)
        assert result["token_address"] == token_addr
        assert result["chain"] == "bsc"
    
    def test_with_pool_address(self):
        """Test with specific pool address."""
        pool_addr = BSC_POOLS["USDT-BNB"]["pancakeswap_v3"]
        result = get_liquidity_bsc("USDT", pool_address=pool_addr)
        assert result["chain"] == "bsc"
        assert len(result["pools"]) > 0
        assert result["pools"][0]["pool_address"] == pool_addr
    
    def test_pools_from_constants(self):
        """Test that pools are fetched from constants."""
        result = get_liquidity_bsc("USDT")
        assert len(result["pools"]) > 0
        assert all("pool_address" in pool for pool in result["pools"])
        assert all("dex" in pool for pool in result["pools"])
    
    def test_bsc_rpc_connection(self, rpc_urls):
        """Test connection to BSC RPC endpoint."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["bsc"]))
        assert w3.is_connected(), "Failed to connect to BSC RPC"
    
    def test_bsc_token_contract_exists(self, rpc_urls, test_token_addresses):
        """Test that token contract exists on BSC chain."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["bsc"]))
        usdc_address = test_token_addresses["bsc"]["USDC"]
        
        # Check if contract exists (has code)
        code = w3.eth.get_code(usdc_address)
        assert len(code) > 0, f"Contract at {usdc_address} does not exist or has no code"
    
    def test_bsc_pool_contract_exists(self, rpc_urls, test_pool_addresses):
        """Test that pool contract exists on BSC chain."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["bsc"]))
        pool_address = test_pool_addresses["bsc"]["USDT-BNB_PANCAKESWAP_V3"]
        
        # Check if pool contract exists
        code = w3.eth.get_code(pool_address)
        assert len(code) > 0, f"Pool contract at {pool_address} does not exist"
    
    def test_bsc_get_latest_block(self, rpc_urls):
        """Test fetching latest block from BSC."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["bsc"]))
        latest_block = w3.eth.block_number
        assert latest_block > 0, "Failed to get latest block number"
        assert isinstance(latest_block, int)
    
    def test_bsc_chain_id(self, rpc_urls):
        """Test that BSC chain ID is correct (56 for mainnet)."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["bsc"]))
        chain_id = w3.eth.chain_id
        assert chain_id == 56, f"Expected chain ID 56 for BSC mainnet, got {chain_id}"

