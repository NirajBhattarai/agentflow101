"""
Bridge execution service for Bridge Agent.

Handles the actual bridge execution logic using EtaBridge.
"""

import random
from typing import Optional
from ..tools import get_bridge_etabridge
from ...balance.tools.hedera import get_balance_hedera
from ...balance.tools.polygon import get_balance_polygon
from ..core.exceptions import InvalidBridgePairError, TokenNotSupportedError


def _validate_bridge_pair(source_chain: str, destination_chain: str) -> None:
    """Validate that bridge pair is supported."""
    if source_chain == destination_chain:
        raise InvalidBridgePairError(source_chain, destination_chain)
    supported_chains = ["hedera", "polygon"]
    if source_chain not in supported_chains or destination_chain not in supported_chains:
        raise InvalidBridgePairError(source_chain, destination_chain)


def _fetch_balance(
    chain: str, account: str, token_address: str, token_symbol: str
) -> float:
    """Fetch balance for account and token."""
    try:
        print(f"🔍 Fetching balance for {account} on {chain} for {token_symbol} (address: {token_address})")
        
        # Use token_symbol for balance lookup (more reliable than address)
        if chain == "hedera":
            result = get_balance_hedera(account, token_address=token_symbol)
        else:
            result = get_balance_polygon(account, token_address=token_symbol)
        
        print(f"📊 Balance result: {result}")
        
        if result.get("balances"):
            for balance_item in result["balances"]:
                # Match by token symbol (most reliable)
                if balance_item.get("token_symbol", "").upper() == token_symbol.upper():
                    balance_str = balance_item.get("balance", "0")
                    balance_float = float(balance_str)
                    print(f"✅ Found balance: {balance_float} {token_symbol}")
                    return balance_float
                
                # Also try matching by token address (for cases where address is provided)
                if token_address and balance_item.get("token_address") == token_address:
                    balance_str = balance_item.get("balance", "0")
                    balance_float = float(balance_str)
                    print(f"✅ Found balance by address: {balance_float} {token_symbol}")
                    return balance_float
                
                # Handle native tokens
                if (
                    token_symbol in ["HBAR", "MATIC"]
                    and balance_item.get("token_type") == "native"
                ):
                    balance_str = balance_item.get("balance", "0")
                    balance_float = float(balance_str)
                    print(f"✅ Found native balance: {balance_float} {token_symbol}")
                    return balance_float
        
        print(f"⚠️ No balance found for {token_symbol} in result")
    except Exception as e:
        print(f"⚠️ Error fetching balance: {e}")
        import traceback
        traceback.print_exc()
    return 0.0


def execute_bridge(
    source_chain: str,
    destination_chain: str,
    token_symbol: str,
    amount: str,
    account_address: Optional[str],
) -> dict:
    """Execute bridge and return bridge data."""
    _validate_bridge_pair(source_chain, destination_chain)
    
    bridge_config = get_bridge_etabridge(
        source_chain,
        destination_chain,
        token_symbol,
        amount,
        account_address or "",
    )
    
    # Extract token address
    token_address = bridge_config.get("token_address", "")
    
    # Check balance
    try:
        amount_float = float(amount)
    except Exception:
        amount_float = 100.0
    
    actual_balance = 0.0
    balance_sufficient = False
    if account_address:
        actual_balance = _fetch_balance(
            source_chain, account_address, token_address, token_symbol
        )
        balance_sufficient = actual_balance >= amount_float
    
    balance_check = None
    if account_address:
        balance_check = {
            "account_address": account_address,
            "token_symbol": token_symbol,
            "balance": f"{actual_balance:.2f}",
            "balance_sufficient": balance_sufficient,
            "required_amount": f"{amount_float:.2f}",
        }
    
    # Build bridge options (include token address for frontend use)
    bridge_options = [
        {
            "bridge_protocol": "EtaBridge",
            "bridge_fee": bridge_config.get("bridge_fee", "0.1%"),
            "estimated_time": bridge_config.get("estimated_time", "~5 minutes"),
            "is_recommended": True,
            "token_address": token_address,  # Include token address for frontend
            "bridge_contract_address": bridge_config.get("bridge_contract_address", ""),
            "source_chain_id": bridge_config.get("source_chain_id", 0),
            "destination_chain_id": bridge_config.get("destination_chain_id", 0),
        }
    ]
    
    # Don't create transaction object yet - only return bridge options
    # Transaction will be created when user executes the bridge from the frontend
    # This matches the swap flow: return options first, user selects and executes
    
    # Check if amount exceeds threshold
    amount_exceeds_threshold = amount_float >= 1000.0
    requires_confirmation = amount_exceeds_threshold
    
    return {
        "source_chain": source_chain,
        "destination_chain": destination_chain,
        "token_symbol": token_symbol,
        "amount": amount,
        "account_address": account_address,
        "balance_check": balance_check,
        "bridge_options": bridge_options,
        "transaction": None,  # No transaction until user executes
        "requires_confirmation": requires_confirmation,
        "amount_exceeds_threshold": amount_exceeds_threshold,
    }

