import json
import os
import pytest

from agents.balance.balance_executor import BalanceAgent


@pytest.mark.asyncio
async def test_polygon_uses_remote_balances(rpc_urls, test_account_addresses):
    # Ensure RPC URL available for remote call
    os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"]) 

    agent = BalanceAgent()
    # Query with explicit polygon + a known EVM address
    query = f"balance polygon {test_account_addresses['polygon']}"
    response = await agent.invoke(query, session_id="test")
    data = json.loads(response)

    assert data["type"] == "balance"
    assert data["chain"] == "polygon"
    assert data["account_address"].lower() == test_account_addresses["polygon"].lower()
    assert isinstance(data["balances"], list)
    assert len(data["balances"]) > 0

    # Expect at least the native MATIC balance
    native = next((b for b in data["balances"] if b["token_type"] == "native"), None)
    assert native is not None
    assert native["token_symbol"] == "MATIC"
    assert "balance" in native and "balance_raw" in native


@pytest.mark.asyncio
async def test_hedera_kept_hardcoded(test_account_addresses):
    agent = BalanceAgent()
    query = "balance hedera 0.0.2"
    response = await agent.invoke(query, session_id="test")
    data = json.loads(response)

    assert data["type"] == "balance"
    assert data["chain"] == "hedera"
    assert data["account_address"] == "0.0.2"
    assert len(data["balances"]) >= 2

    # Check hardcoded native HBAR
    hbar = next((b for b in data["balances"] if b["token_symbol"] == "HBAR"), None)
    assert hbar is not None
    assert hbar["balance"] == "1500.0"
    assert hbar["balance_raw"] == "150000000000"
    assert hbar["decimals"] == 8


@pytest.mark.asyncio
async def test_all_combines_polygon_remote_and_hedera_hardcoded(rpc_urls, test_account_addresses):
    os.environ.setdefault("POLYGON_RPC_URL", rpc_urls["polygon"]) 

    agent = BalanceAgent()
    # Address can be either; we still expect both chains
    query = f"balance all {test_account_addresses['polygon']}"
    response = await agent.invoke(query, session_id="test")
    data = json.loads(response)

    assert data["type"] == "balance"
    assert data["chain"] == "all"
    balances = data["balances"]
    assert isinstance(balances, list)
    assert len(balances) >= 2

    # Hedera hardcoded presence
    hbar = next((b for b in balances if b["token_symbol"] == "HBAR"), None)
    assert hbar is not None
    assert hbar["balance"] == "1500.0"

    # Polygon remote presence (native MATIC expected)
    matic = next((b for b in balances if b["token_type"] == "native" and b["token_symbol"] == "MATIC"), None)
    assert matic is not None

