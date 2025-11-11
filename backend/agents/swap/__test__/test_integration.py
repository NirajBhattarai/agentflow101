"""
Integration tests for Swap Agent.

Tests the full flow from executor -> agent -> services -> tools.
"""

import json
import os
import pytest
from typing import List

from agents.swap.executor import SwapExecutor
from agents.swap.agent import SwapAgent


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
        self.events: List[dict] = []

    async def enqueue_event(self, event: dict):
        """Enqueue an event."""
        self.events.append(event)

    def get_last_event(self) -> dict:
        """Get the last enqueued event."""
        return self.events[-1] if self.events else None

    def clear(self):
        """Clear all events."""
        self.events = []


class TestSwapAgentIntegration:
    """Integration tests for SwapAgent."""

    @pytest.mark.asyncio
    async def test_agent_hedera_swap_query(self, test_account_addresses):
        """Test agent handles Hedera swap query correctly."""
        agent = SwapAgent()
        query = f"Swap 0.01 HBAR to USDC on Hedera for account {test_account_addresses['hedera']}"
        response = await agent.invoke(query, session_id="test")

        data = json.loads(response)
        assert data["type"] == "swap"
        assert data["chain"] == "hedera"
        assert data["token_in_symbol"] == "HBAR"
        assert data["token_out_symbol"] == "USDC"
        assert data["amount_in"] == "0.01"
        assert data.get("transaction") is not None

    @pytest.mark.asyncio
    async def test_agent_polygon_swap_query(self, rpc_urls, test_account_addresses):
        """Test agent handles Polygon swap query correctly."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        agent = SwapAgent()
        query = f"Swap 0.1 MATIC to USDC on Polygon for account {test_account_addresses['polygon']}"
        response = await agent.invoke(query, session_id="test")

        data = json.loads(response)
        assert data["type"] == "swap"
        assert data["chain"] == "polygon"
        assert data["token_in_symbol"] == "MATIC"
        assert data["token_out_symbol"] == "USDC"
        assert data.get("transaction") is not None

    @pytest.mark.asyncio
    async def test_agent_token_detection(self):
        """Test agent correctly detects tokens from query."""
        agent = SwapAgent()

        query1 = "Swap 0.2 USDC to HBAR on Hedera"
        response1 = await agent.invoke(query1, session_id="test")
        data1 = json.loads(response1)
        assert data1["token_in_symbol"] == "USDC"
        assert data1["token_out_symbol"] == "HBAR"

        query2 = "Swap HBAR for USDC on Hedera"
        response2 = await agent.invoke(query2, session_id="test")
        data2 = json.loads(response2)
        assert data2["token_in_symbol"] == "HBAR"
        assert data2["token_out_symbol"] == "USDC"

    @pytest.mark.asyncio
    async def test_agent_chain_detection(self):
        """Test agent correctly detects chain from query."""
        agent = SwapAgent()

        query1 = "Swap 0.1 HBAR to USDC on Hedera"
        response1 = await agent.invoke(query1, session_id="test")
        data1 = json.loads(response1)
        assert data1["chain"] == "hedera"

        query2 = "Swap 0.1 MATIC to USDC on Polygon"
        response2 = await agent.invoke(query2, session_id="test")
        data2 = json.loads(response2)
        assert data2["chain"] == "polygon"

    @pytest.mark.asyncio
    async def test_agent_response_validation(self, test_account_addresses):
        """Test agent response is valid JSON and follows schema."""
        agent = SwapAgent()
        query = f"Swap 0.01 HBAR to USDC on Hedera for account {test_account_addresses['hedera']}"
        response = await agent.invoke(query, session_id="test")

        data = json.loads(response)
        assert "type" in data
        assert "chain" in data
        assert "token_in_symbol" in data
        assert "token_out_symbol" in data
        assert "amount_in" in data
        if data.get("transaction"):
            assert "token_in_address" in data["transaction"]
            assert "token_out_address" in data["transaction"]
            assert "amount_out" in data["transaction"]
            assert "status" in data["transaction"]


class TestSwapExecutorIntegration:
    """Integration tests for SwapExecutor (A2A Protocol)."""

    @pytest.mark.asyncio
    async def test_executor_successful_execution(self, test_account_addresses):
        """Test executor successfully processes a swap request."""
        executor = SwapExecutor()
        context = MockRequestContext(
            user_input=f"Swap 0.01 HBAR to USDC on Hedera for account {test_account_addresses['hedera']}",
            context_id="test-executor-123",
        )
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        assert len(event_queue.events) > 0
        last_event = event_queue.get_last_event()
        assert last_event is not None

    @pytest.mark.asyncio
    async def test_executor_polygon_execution(self, rpc_urls, test_account_addresses):
        """Test executor handles Polygon requests."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        executor = SwapExecutor()
        context = MockRequestContext(
            user_input=f"Swap 0.1 MATIC to USDC on Polygon for account {test_account_addresses['polygon']}",
        )
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        assert len(event_queue.events) > 0

    @pytest.mark.asyncio
    async def test_executor_error_handling(self):
        """Test executor handles errors gracefully."""
        executor = SwapExecutor()
        context = MockRequestContext(user_input="Invalid swap query")
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        assert len(event_queue.events) > 0

    @pytest.mark.asyncio
    async def test_executor_cancel_not_supported(self):
        """Test executor cancel method raises appropriate error."""
        executor = SwapExecutor()
        context = MockRequestContext(user_input="test")
        event_queue = MockEventQueue()

        with pytest.raises(Exception) as exc_info:
            await executor.cancel(context, event_queue)

        assert (
            "not supported" in str(exc_info.value).lower()
            or "cancel" in str(exc_info.value).lower()
        )


class TestEndToEndSwapIntegration:
    """End-to-end integration tests covering full swap flow."""

    @pytest.mark.asyncio
    async def test_full_flow_hedera(self, test_account_addresses):
        """Test complete flow: Executor -> Agent -> Services -> Tools for Hedera."""
        executor = SwapExecutor()
        context = MockRequestContext(
            user_input=f"Swap 0.01 HBAR to USDC on Hedera for account {test_account_addresses['hedera']}",
        )
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        assert len(event_queue.events) > 0

        agent = SwapAgent()
        response = await agent.invoke(
            context.get_user_input(), session_id=context.context_id
        )
        data = json.loads(response)

        assert data["type"] == "swap"
        assert data["chain"] == "hedera"
        assert data["token_in_symbol"] == "HBAR"
        assert data["token_out_symbol"] == "USDC"

    @pytest.mark.asyncio
    async def test_full_flow_polygon(self, rpc_urls, test_account_addresses):
        """Test complete flow: Executor -> Agent -> Services -> Tools for Polygon."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        executor = SwapExecutor()
        context = MockRequestContext(
            user_input=f"Swap 0.1 MATIC to USDC on Polygon for account {test_account_addresses['polygon']}",
        )
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        assert len(event_queue.events) > 0

        agent = SwapAgent()
        response = await agent.invoke(
            context.get_user_input(), session_id=context.context_id
        )
        data = json.loads(response)

        assert data["type"] == "swap"
        assert data["chain"] == "polygon"
        assert data["token_in_symbol"] == "MATIC"
        assert data["token_out_symbol"] == "USDC"
