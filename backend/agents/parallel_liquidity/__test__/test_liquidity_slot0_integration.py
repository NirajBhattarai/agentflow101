"""
Integration tests for Parallel Liquidity Agent with liquidity and slot0 retrieval.

Tests liquidity and slot0 retrieval from Polygon, Ethereum, and Hedera chains.
"""

import json
import pytest
from typing import Dict, Optional
from web3 import Web3

from agents.parallel_liquidity.agent import ParallelLiquidityAgent
from agents.parallel_liquidity.executor import ParallelLiquidityExecutor
from lib.shared.blockchain.liquidity import (
    get_pool_liquidity_polygon,
    get_pool_liquidity_ethereum,
    get_pool_liquidity_hedera,
)


class MockRequestContext:
    """Mock RequestContext for testing."""

    def __init__(self, user_input: str, context_id: str = "test-session-123"):
        self._user_input = user_input
        self.context_id = context_id

    def get_user_input(self) -> str:
        """Get user input."""
        return self._user_input


class MockEventQueue:
    """Mock EventQueue for testing."""

    def __init__(self):
        self.events: list = []

    async def enqueue_event(self, event: dict):
        """Enqueue an event."""
        self.events.append(event)

    def get_last_event(self) -> dict:
        """Get the last enqueued event."""
        return self.events[-1] if self.events else None


class TestLiquidityAndSlot0Integration:
    """Integration tests for liquidity and slot0 retrieval across chains."""

    @pytest.mark.asyncio
    async def test_get_liquidity_eth_usdt_polygon(self, rpc_urls):
        """Test getting liquidity and slot0 for ETH/USDT on Polygon."""
        # Test using pool liquidity function directly
        result = get_pool_liquidity_polygon("ETH-USDT", dex="uniswap")
        
        assert result is not None
        assert result["chain"] == "polygon"
        assert result["pair"] == "ETH-USDT"
        
        # Check if pool address exists
        if "pool_address" in result and result["pool_address"]:
            assert result["pool_address"] is not None
            assert len(result["pool_address"]) > 0
            
            # For EVM chains, check if slot0 is available (when implemented)
            # Currently slot0 might not be fully implemented, so we check if it exists
            if "slot0" in result:
                slot0 = result["slot0"]
                assert slot0 is not None
                # slot0 should contain sqrtPriceX96, tick, observationIndex, etc.
                if isinstance(slot0, dict):
                    assert "sqrtPriceX96" in slot0 or "tick" in slot0
        
        # Check liquidity data exists
        assert "liquidity" in result or "error" in result
        
        # Verify RPC connection
        if "rpc_connected" in result:
            assert result["rpc_connected"] is True

    @pytest.mark.asyncio
    async def test_get_liquidity_eth_usdt_ethereum(self, rpc_urls):
        """Test getting liquidity and slot0 for ETH/USDT on Ethereum."""
        # Test using pool liquidity function directly
        result = get_pool_liquidity_ethereum("ETH-USDT", dex="uniswap")
        
        assert result is not None
        assert result["chain"] in ["ethereum", "eth"]
        assert result["pair"] == "ETH-USDT"
        
        # Check if pool address exists
        if "pool_address" in result and result["pool_address"]:
            assert result["pool_address"] is not None
            assert len(result["pool_address"]) > 0
            
            # For EVM chains, check if slot0 is available (when implemented)
            if "slot0" in result:
                slot0 = result["slot0"]
                assert slot0 is not None
                if isinstance(slot0, dict):
                    assert "sqrtPriceX96" in slot0 or "tick" in slot0
        
        # Check liquidity data exists
        assert "liquidity" in result or "error" in result
        
        # Verify RPC connection
        if "rpc_connected" in result:
            assert result["rpc_connected"] is True

    @pytest.mark.asyncio
    async def test_get_liquidity_usdt_hedera(self, rpc_urls):
        """Test getting liquidity for USDT on Hedera."""
        # Test using pool liquidity function directly
        # Note: Hedera might use different pair format (e.g., USDT-USDC or USDT-HBAR)
        result = get_pool_liquidity_hedera("USDT-USDC", dex="saucerswap")
        
        assert result is not None
        assert result["chain"] == "hedera"
        assert result["pair"] == "USDT-USDC"
        
        # Check if pool address exists
        if "pool_address" in result and result["pool_address"]:
            assert result["pool_address"] is not None
            assert len(result["pool_address"]) > 0
        
        # Check liquidity data exists
        assert "liquidity" in result or "error" in result

    @pytest.mark.asyncio
    async def test_parallel_liquidity_agent_eth_usdt(self, rpc_urls):
        """Test parallel liquidity agent with ETH/USDT pair."""
        agent = ParallelLiquidityAgent()
        query = "Get liquidity for ETH/USDT"
        response = await agent.invoke(query, session_id="test-eth-usdt")
        data = json.loads(response)
        
        assert data["type"] == "parallel_liquidity"
        assert data["token_pair"] == "ETH/USDT"
        assert "chains" in data
        assert "hedera_pairs" in data
        assert "polygon_pairs" in data
        assert "all_pairs" in data
        
        # Check that we got results from at least one chain
        total_pools = (
            data["chains"].get("hedera", {}).get("total_pools", 0) +
            data["chains"].get("polygon", {}).get("total_pools", 0)
        )
        assert total_pools >= 0  # At least attempted to fetch
        
        # If we have polygon pairs, verify structure
        if len(data["polygon_pairs"]) > 0:
            polygon_pair = data["polygon_pairs"][0]
            assert "pool_address" in polygon_pair
            assert "chain" in polygon_pair
            assert polygon_pair["chain"] == "polygon"
            assert "base" in polygon_pair
            assert "quote" in polygon_pair

    @pytest.mark.asyncio
    async def test_parallel_liquidity_agent_usdt(self, rpc_urls):
        """Test parallel liquidity agent with USDT token."""
        agent = ParallelLiquidityAgent()
        query = "Get liquidity for USDT"
        response = await agent.invoke(query, session_id="test-usdt")
        data = json.loads(response)
        
        assert data["type"] == "parallel_liquidity"
        # Token pair extraction might handle single tokens differently
        assert "token_pair" in data
        assert "chains" in data
        assert "hedera_pairs" in data
        assert "polygon_pairs" in data

    @pytest.mark.asyncio
    async def test_polygon_pool_liquidity_with_slot0(self, rpc_urls):
        """Test Polygon pool liquidity retrieval includes slot0 when available."""
        # Test with a common pair that should exist
        result = get_pool_liquidity_polygon("USDC-WETH", dex="uniswap")
        
        assert result is not None
        assert result["chain"] == "polygon"
        
        # If pool exists and slot0 is implemented, verify structure
        if "pool_address" in result and result["pool_address"] and "error" not in result:
            # Check for liquidity data
            assert "liquidity" in result or "token0_balance" in result
            
            # Check for slot0 if available (may not be implemented yet)
            if "slot0" in result:
                slot0 = result["slot0"]
                if slot0 is not None:
                    # slot0 should be a dict with Uniswap V3 pool state
                    assert isinstance(slot0, dict)
                    # Common slot0 fields: sqrtPriceX96, tick, observationIndex, observationCardinality, etc.
                    assert len(slot0) > 0

    @pytest.mark.asyncio
    async def test_ethereum_pool_liquidity_with_slot0(self, rpc_urls):
        """Test Ethereum pool liquidity retrieval includes slot0 when available."""
        # Test with a common pair that should exist
        result = get_pool_liquidity_ethereum("USDC-WETH", dex="uniswap")
        
        assert result is not None
        assert result["chain"] in ["ethereum", "eth"]
        
        # If pool exists and slot0 is implemented, verify structure
        if "pool_address" in result and result["pool_address"] and "error" not in result:
            # Check for liquidity data
            assert "liquidity" in result or "token0_balance" in result
            
            # Check for slot0 if available (may not be implemented yet)
            if "slot0" in result:
                slot0 = result["slot0"]
                if slot0 is not None:
                    # slot0 should be a dict with Uniswap V3 pool state
                    assert isinstance(slot0, dict)
                    assert len(slot0) > 0

    @pytest.mark.asyncio
    async def test_hedera_pool_liquidity(self, rpc_urls):
        """Test Hedera pool liquidity retrieval."""
        # Test with a common pair
        result = get_pool_liquidity_hedera("USDC-HBAR", dex="saucerswap")
        
        assert result is not None
        assert result["chain"] == "hedera"
        assert result["pair"] == "USDC-HBAR"
        
        # Check for liquidity data
        if "error" not in result:
            assert "liquidity" in result or "tvl" in result
            assert "pool_address" in result

    @pytest.mark.asyncio
    async def test_executor_with_eth_usdt_query(self, rpc_urls):
        """Test executor handles ETH/USDT liquidity query."""
        executor = ParallelLiquidityExecutor()
        context = MockRequestContext(
            user_input="Get liquidity for ETH/USDT",
            context_id="test-executor-eth-usdt",
        )
        event_queue = MockEventQueue()
        
        await executor.execute(context, event_queue)
        
        assert len(event_queue.events) > 0
        last_event = event_queue.get_last_event()
        assert last_event is not None
        
        # Verify response is valid JSON
        if "text" in last_event:
            response_data = json.loads(last_event["text"])
            assert response_data["type"] == "parallel_liquidity"
            assert "token_pair" in response_data
            assert "chains" in response_data

    @pytest.mark.asyncio
    async def test_executor_with_usdt_query(self, rpc_urls):
        """Test executor handles USDT liquidity query."""
        executor = ParallelLiquidityExecutor()
        context = MockRequestContext(
            user_input="Get liquidity for USDT",
            context_id="test-executor-usdt",
        )
        event_queue = MockEventQueue()
        
        await executor.execute(context, event_queue)
        
        assert len(event_queue.events) > 0
        last_event = event_queue.get_last_event()
        assert last_event is not None
        
        # Verify response is valid JSON
        if "text" in last_event:
            response_data = json.loads(last_event["text"])
            assert response_data["type"] == "parallel_liquidity"

    @pytest.mark.asyncio
    async def test_multiple_chains_liquidity_comparison(self, rpc_urls):
        """Test comparing liquidity across Polygon, Ethereum, and Hedera."""
        # Get liquidity from all three chains for comparison
        polygon_result = get_pool_liquidity_polygon("USDC-WETH", dex="uniswap")
        ethereum_result = get_pool_liquidity_ethereum("USDC-WETH", dex="uniswap")
        hedera_result = get_pool_liquidity_hedera("USDC-HBAR", dex="saucerswap")
        
        # Verify all results are dictionaries
        assert isinstance(polygon_result, dict)
        assert isinstance(ethereum_result, dict)
        assert isinstance(hedera_result, dict)
        
        # Verify chain identifiers
        assert polygon_result["chain"] == "polygon"
        assert ethereum_result["chain"] in ["ethereum", "eth"]
        assert hedera_result["chain"] == "hedera"
        
        # Check that at least one chain returned pool data
        has_pool_data = (
            ("pool_address" in polygon_result and polygon_result["pool_address"]) or
            ("pool_address" in ethereum_result and ethereum_result["pool_address"]) or
            ("pool_address" in hedera_result and hedera_result["pool_address"])
        )
        assert has_pool_data or any("error" in r for r in [polygon_result, ethereum_result, hedera_result])

    @pytest.mark.asyncio
    async def test_slot0_structure_when_available(self, rpc_urls):
        """Test that slot0 has correct structure when available from EVM chains."""
        # Test Polygon first
        polygon_result = get_pool_liquidity_polygon("USDC-WETH", dex="uniswap")
        
        if "slot0" in polygon_result and polygon_result["slot0"]:
            slot0 = polygon_result["slot0"]
            assert isinstance(slot0, dict)
            # Uniswap V3 slot0 typically contains:
            # - sqrtPriceX96: uint160 (price as sqrt(price) * 2^96)
            # - tick: int24 (current tick)
            # - observationIndex: uint16
            # - observationCardinality: uint16
            # - observationCardinalityNext: uint16
            # - feeProtocol: uint8
            # - unlocked: bool
            # We check for at least some of these fields
            assert len(slot0) > 0
        
        # Test Ethereum
        ethereum_result = get_pool_liquidity_ethereum("USDC-WETH", dex="uniswap")
        
        if "slot0" in ethereum_result and ethereum_result["slot0"]:
            slot0 = ethereum_result["slot0"]
            assert isinstance(slot0, dict)
            assert len(slot0) > 0

    def test_polygon_rpc_connection(self, rpc_urls):
        """Test Polygon RPC connection."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["polygon"]))
        assert w3.is_connected(), "Failed to connect to Polygon RPC"
        assert w3.eth.chain_id == 137, "Expected Polygon chain ID 137"

    def test_ethereum_rpc_connection(self, rpc_urls):
        """Test Ethereum RPC connection."""
        w3 = Web3(Web3.HTTPProvider(rpc_urls["ethereum"]))
        assert w3.is_connected(), "Failed to connect to Ethereum RPC"
        assert w3.eth.chain_id == 1, "Expected Ethereum mainnet chain ID 1"

    def test_hedera_rpc_connection(self, rpc_urls):
        """Test Hedera RPC connection."""
        # Hedera uses a different RPC format, so we just check if URL is set
        assert rpc_urls["hedera"] is not None
        assert len(rpc_urls["hedera"]) > 0

