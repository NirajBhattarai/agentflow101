"""
Unit tests for Ethereum liquidity tool.
Tests fetch actual data from Ethereum chain using RPC.
"""
import pytest
from web3 import Web3
from agents.liquidity.tools.ethereum import get_liquidity_ethereum
from agents.liquidity.tools.constants import ETHEREUM_TOKENS, ETHEREUM_POOLS


class TestEthereumLiquidity:
    """Test cases for Ethereum liquidity fetching."""
    
    def test_token_address_lookup(self):
        """Test that token symbols are resolved to addresses."""
        result = get_liquidity_ethereum("USDC")
        assert result["token_address"] == ETHEREUM_TOKENS["USDC"]
        assert result["chain"] == "ethereum"
        assert "pools" in result
    
    def test_with_address_directly(self):
        """Test with direct token address."""
        token_addr = ETHEREUM_TOKENS["USDC"]
        result = get_liquidity_ethereum(token_addr)
        assert result["token_address"] == token_addr
        assert result["chain"] == "ethereum"
    
    def test_with_pool_address(self):
        """Test with specific pool address."""
        pool_addr = ETHEREUM_POOLS["USDC-ETH"]["uniswap_v3"]
        result = get_liquidity_ethereum("USDC", pool_address=pool_addr)
        assert result["chain"] == "ethereum"
        assert len(result["pools"]) > 0
        assert result["pools"][0]["pool_address"] == pool_addr
    
    def test_pools_from_constants(self):
        """Test that pools are fetched from constants."""
        result = get_liquidity_ethereum("USDC")
        assert len(result["pools"]) > 0
        assert all("pool_address" in pool for pool in result["pools"])
        assert all("dex" in pool for pool in result["pools"])
    
    def test_ethereum_rpc_connection(self, rpc_urls):
        """Test connection to Ethereum RPC endpoint."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["ethereum"]))
        assert w3.is_connected(), "Failed to connect to Ethereum RPC"
    
    def test_ethereum_token_contract_exists(self, rpc_urls, test_token_addresses):
        """Test that token contract exists on Ethereum chain."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["ethereum"]))
        usdc_address = test_token_addresses["ethereum"]["USDC"]
        
        # Check if contract exists (has code)
        code = w3.eth.get_code(usdc_address)
        assert len(code) > 0, f"Contract at {usdc_address} does not exist or has no code"
    
    def test_ethereum_pool_contract_exists(self, rpc_urls, test_pool_addresses):
        """Test that pool contract exists on Ethereum chain."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["ethereum"]))
        pool_address = test_pool_addresses["ethereum"]["USDC-ETH_UNISWAP_V3"]
        
        # Check if pool contract exists
        code = w3.eth.get_code(pool_address)
        assert len(code) > 0, f"Pool contract at {pool_address} does not exist"
    
    def test_ethereum_get_latest_block(self, rpc_urls):
        """Test fetching latest block from Ethereum."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["ethereum"]))
        latest_block = w3.eth.block_number
        assert latest_block > 0, "Failed to get latest block number"
        assert isinstance(latest_block, int)
    
    def test_ethereum_token_balance_check(self, rpc_urls, test_token_addresses):
        """Test checking token balance via RPC (if ERC20 ABI available)."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["ethereum"]))
        # Simple connection test - full ERC20 balance check would need ABI
        assert w3.is_connected(), "RPC connection required for balance checks"

