"""
Integration tests for Balance Agent.

Tests the full flow from executor -> agent -> services -> tools.
"""

import json
import os
import pytest
from typing import List

from agents.balance.executor import BalanceExecutor
from agents.balance.agent import BalanceAgent


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


class TestBalanceAgentIntegration:
    """Integration tests for BalanceAgent."""

    @pytest.mark.asyncio
    async def test_agent_polygon_query(self, rpc_urls, test_account_addresses):
        """Test agent handles Polygon query correctly."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        agent = BalanceAgent()
        query = f"Get balance for {test_account_addresses['polygon']} on Polygon"
        response = await agent.invoke(query, session_id="test")

        # Validate response structure
        data = json.loads(response)
        assert data["type"] == "balance"
        assert data["chain"] == "polygon"
        assert (
            data["account_address"].lower() == test_account_addresses["polygon"].lower()
        )
        assert isinstance(data["balances"], list)
        assert len(data["balances"]) > 0

        # Check native balance
        native = next(
            (b for b in data["balances"] if b["token_type"] == "native"), None
        )
        assert native is not None
        assert native["token_symbol"] == "MATIC"

    @pytest.mark.asyncio
    async def test_agent_hedera_query(self, test_account_addresses):
        """Test agent handles Hedera query correctly."""
        agent = BalanceAgent()
        query = (
            f"Get HBAR balance for account {test_account_addresses['hedera']} on Hedera"
        )
        response = await agent.invoke(query, session_id="test")

        # Validate response structure
        data = json.loads(response)
        assert data["type"] == "balance"
        assert data["chain"] == "hedera"
        assert data["account_address"] == test_account_addresses["hedera"]
        assert isinstance(data["balances"], list)

        # Check native HBAR balance
        hbar = next(
            (
                b
                for b in data["balances"]
                if b["token_type"] == "native" and b["token_symbol"] == "HBAR"
            ),
            None,
        )
        assert hbar is not None
        assert hbar["decimals"] == 8

    @pytest.mark.asyncio
    async def test_agent_all_chains_query(self, rpc_urls, test_account_addresses):
        """Test agent handles all chains query correctly."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        agent = BalanceAgent()
        query = f"Get all balances for {test_account_addresses['polygon']} across all chains"
        response = await agent.invoke(query, session_id="test")

        # Validate response structure
        data = json.loads(response)
        assert data["type"] == "balance"
        assert data["chain"] == "all"
        assert isinstance(data["balances"], list)
        assert len(data["balances"]) >= 2

        # Check both chains are represented
        chains_in_response = {b.get("chain") for b in data["balances"] if "chain" in b}
        assert "polygon" in chains_in_response
        assert "hedera" in chains_in_response

    @pytest.mark.asyncio
    async def test_agent_address_detection_from_query(
        self, rpc_urls, test_account_addresses
    ):
        """Test agent correctly detects addresses from different query formats."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        agent = BalanceAgent()

        # Test EVM address detection
        query1 = f"Check balance for {test_account_addresses['polygon']}"
        response1 = await agent.invoke(query1, session_id="test")
        data1 = json.loads(response1)
        assert (
            data1["account_address"].lower()
            == test_account_addresses["polygon"].lower()
        )

        # Test Hedera address detection
        query2 = f"Balance for {test_account_addresses['hedera']}"
        response2 = await agent.invoke(query2, session_id="test")
        data2 = json.loads(response2)
        assert data2["account_address"] == test_account_addresses["hedera"]

    @pytest.mark.asyncio
    async def test_agent_chain_detection_from_query(
        self, rpc_urls, test_account_addresses
    ):
        """Test agent correctly detects chain from query text."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        agent = BalanceAgent()

        # Test explicit chain mention
        query1 = "Get balance on Polygon for 0x1234567890123456789012345678901234567890"
        response1 = await agent.invoke(query1, session_id="test")
        data1 = json.loads(response1)
        assert data1["chain"] == "polygon"

        query2 = "Show me Hedera balance for 0.0.123456"
        response2 = await agent.invoke(query2, session_id="test")
        data2 = json.loads(response2)
        assert data2["chain"] == "hedera"

        query3 = "Get all balances across all chains for 0x1234567890123456789012345678901234567890"
        response3 = await agent.invoke(query3, session_id="test")
        data3 = json.loads(response3)
        assert data3["chain"] == "all"

    @pytest.mark.asyncio
    async def test_agent_error_handling_invalid_address(self):
        """Test agent handles invalid address gracefully."""
        agent = BalanceAgent()
        query = "Get balance for invalid-address-123"
        response = await agent.invoke(query, session_id="test")

        # Should return error response, not crash
        data = json.loads(response)
        assert "error" in data or len(data.get("balances", [])) == 0

    @pytest.mark.asyncio
    async def test_agent_response_validation(self, rpc_urls, test_account_addresses):
        """Test agent response is valid JSON and follows schema."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        agent = BalanceAgent()
        query = f"Get balance for {test_account_addresses['polygon']} on Polygon"
        response = await agent.invoke(query, session_id="test")

        # Should be valid JSON
        data = json.loads(response)

        # Should follow expected schema
        assert "type" in data
        assert "chain" in data
        assert "account_address" in data
        assert "balances" in data
        assert "total_usd_value" in data

        # Balances should be list of objects with required fields
        for balance in data["balances"]:
            assert "token_type" in balance
            assert "token_symbol" in balance
            assert "token_address" in balance
            assert "balance" in balance
            assert "balance_raw" in balance
            assert "decimals" in balance


class TestBalanceExecutorIntegration:
    """Integration tests for BalanceExecutor (A2A Protocol)."""

    @pytest.mark.asyncio
    async def test_executor_successful_execution(
        self, rpc_urls, test_account_addresses
    ):
        """Test executor successfully processes a request."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        executor = BalanceExecutor()
        context = MockRequestContext(
            user_input=f"Get balance for {test_account_addresses['polygon']} on Polygon",
            context_id="test-executor-123",
        )
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        # Check event was enqueued
        assert len(event_queue.events) > 0
        last_event = event_queue.get_last_event()
        assert last_event is not None

        # Check event contains valid balance data
        # The event structure depends on A2A protocol, but should contain the response
        event_str = (
            json.dumps(last_event) if isinstance(last_event, dict) else str(last_event)
        )
        assert "balance" in event_str.lower() or "matic" in event_str.lower()

    @pytest.mark.asyncio
    async def test_executor_hedera_execution(self, test_account_addresses):
        """Test executor handles Hedera requests."""
        executor = BalanceExecutor()
        context = MockRequestContext(
            user_input=f"Get HBAR balance for {test_account_addresses['hedera']} on Hedera",
            context_id="test-executor-hedera",
        )
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        # Check event was enqueued
        assert len(event_queue.events) > 0
        last_event = event_queue.get_last_event()
        assert last_event is not None

    @pytest.mark.asyncio
    async def test_executor_all_chains_execution(
        self, rpc_urls, test_account_addresses
    ):
        """Test executor handles all chains requests."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        executor = BalanceExecutor()
        context = MockRequestContext(
            user_input=f"Get all balances for {test_account_addresses['polygon']} across all chains",
            context_id="test-executor-all",
        )
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        # Check event was enqueued
        assert len(event_queue.events) > 0
        last_event = event_queue.get_last_event()
        assert last_event is not None

    @pytest.mark.asyncio
    async def test_executor_error_handling(self):
        """Test executor handles errors gracefully."""
        executor = BalanceExecutor()

        # Create a context that might cause issues
        context = MockRequestContext(
            user_input="Get balance for invalid-address",
            context_id="test-executor-error",
        )
        event_queue = MockEventQueue()

        # Should not raise exception, should enqueue error response
        await executor.execute(context, event_queue)

        # Should still enqueue a response (even if error)
        assert len(event_queue.events) > 0

    @pytest.mark.asyncio
    async def test_executor_session_id_extraction(
        self, rpc_urls, test_account_addresses
    ):
        """Test executor correctly extracts session ID from context."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        executor = BalanceExecutor()
        custom_session_id = "custom-session-456"
        context = MockRequestContext(
            user_input=f"Get balance for {test_account_addresses['polygon']}",
            context_id=custom_session_id,
        )
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        # Should process without error
        assert len(event_queue.events) > 0

    @pytest.mark.asyncio
    async def test_executor_cancel_not_supported(self):
        """Test executor cancel method raises appropriate error."""
        executor = BalanceExecutor()
        context = MockRequestContext(user_input="test")
        event_queue = MockEventQueue()

        with pytest.raises(Exception) as exc_info:
            await executor.cancel(context, event_queue)

        assert (
            "not supported" in str(exc_info.value).lower()
            or "cancel" in str(exc_info.value).lower()
        )


class TestEndToEndIntegration:
    """End-to-end integration tests covering full flow."""

    @pytest.mark.asyncio
    async def test_full_flow_polygon(self, rpc_urls, test_account_addresses):
        """Test complete flow: Executor -> Agent -> Services -> Tools for Polygon."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        # Setup
        executor = BalanceExecutor()
        context = MockRequestContext(
            user_input=f"Get balance for {test_account_addresses['polygon']} on Polygon",
        )
        event_queue = MockEventQueue()

        # Execute
        await executor.execute(context, event_queue)

        # Verify
        assert len(event_queue.events) > 0

        # Get response from agent directly to verify structure
        agent = BalanceAgent()
        response = await agent.invoke(
            context.get_user_input(), session_id=context.context_id
        )
        data = json.loads(response)

        assert data["type"] == "balance"
        assert data["chain"] == "polygon"
        assert len(data["balances"]) > 0

    @pytest.mark.asyncio
    async def test_full_flow_hedera(self, test_account_addresses):
        """Test complete flow: Executor -> Agent -> Services -> Tools for Hedera."""
        executor = BalanceExecutor()
        context = MockRequestContext(
            user_input=f"Get HBAR balance for {test_account_addresses['hedera']} on Hedera",
        )
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        assert len(event_queue.events) > 0

        # Verify agent response
        agent = BalanceAgent()
        response = await agent.invoke(
            context.get_user_input(), session_id=context.context_id
        )
        data = json.loads(response)

        assert data["type"] == "balance"
        assert data["chain"] == "hedera"
        assert len(data["balances"]) > 0

    @pytest.mark.asyncio
    async def test_full_flow_all_chains(self, rpc_urls, test_account_addresses):
        """Test complete flow for all chains."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        executor = BalanceExecutor()
        context = MockRequestContext(
            user_input=f"Get all balances for {test_account_addresses['polygon']} across all chains",
        )
        event_queue = MockEventQueue()

        await executor.execute(context, event_queue)

        assert len(event_queue.events) > 0

        # Verify agent response
        agent = BalanceAgent()
        response = await agent.invoke(
            context.get_user_input(), session_id=context.context_id
        )
        data = json.loads(response)

        assert data["type"] == "balance"
        assert data["chain"] == "all"
        assert len(data["balances"]) >= 2

        # Verify chains are tagged
        chains = {b.get("chain") for b in data["balances"] if "chain" in b}
        assert "polygon" in chains
        assert "hedera" in chains

    @pytest.mark.asyncio
    async def test_response_consistency(self, rpc_urls, test_account_addresses):
        """Test that executor and agent return consistent responses."""
        os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"])

        query = f"Get balance for {test_account_addresses['polygon']} on Polygon"

        # Get response from agent
        agent = BalanceAgent()
        agent_response = await agent.invoke(query, session_id="test")

        # Get response from executor
        executor = BalanceExecutor()
        context = MockRequestContext(user_input=query)
        event_queue = MockEventQueue()
        await executor.execute(context, event_queue)

        # Both should produce valid JSON
        agent_data = json.loads(agent_response)
        assert agent_data["type"] == "balance"
        assert agent_data["chain"] == "polygon"

        # Executor should have enqueued the response
        assert len(event_queue.events) > 0


class TestErrorScenariosIntegration:
    """Integration tests for error scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_address_handling(self):
        """Test handling of invalid addresses."""
        agent = BalanceAgent()
        query = "Get balance for not-an-address-123"
        response = await agent.invoke(query, session_id="test")

        # Should return valid response (with error or empty balances)
        data = json.loads(response)
        assert "type" in data
        assert "chain" in data
        assert "account_address" in data

    @pytest.mark.asyncio
    async def test_missing_rpc_url_handling(self):
        """Test handling when RPC URL is missing."""
        # Remove POLYGON_RPC_URL temporarily
        original_url = os.environ.pop("POLYGON_RPC_URL", None)

        try:
            agent = BalanceAgent()
            query = (
                "Get balance for 0x1234567890123456789012345678901234567890 on Polygon"
            )
            response = await agent.invoke(query, session_id="test")

            # Should handle gracefully (may return error or empty balances)
            data = json.loads(response)
            assert "type" in data
        finally:
            # Restore original URL
            if original_url:
                os.environ["POLYGON_RPC_URL"] = original_url

    @pytest.mark.asyncio
    async def test_executor_handles_agent_exception(self):
        """Test executor handles exceptions from agent gracefully."""
        executor = BalanceExecutor()
        context = MockRequestContext(user_input="")
        event_queue = MockEventQueue()

        # Should not raise exception
        await executor.execute(context, event_queue)

        # Should enqueue error response
        assert len(event_queue.events) > 0
