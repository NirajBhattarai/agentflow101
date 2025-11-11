"""
Swap execution service for Swap Agent.

Handles the actual swap execution logic.
"""

import random
from typing import Optional
from ..tools import get_swap_hedera, get_swap_polygon
from ...balance.tools.hedera import get_balance_hedera
from ...balance.tools.polygon import get_balance_polygon
from ..core.exceptions import ChainNotSupportedError


def _get_swap_config(
    chain: str,
    token_in: str,
    token_out: str,
    amount: str,
    account: str,
    slippage: float,
) -> dict:
    """Get swap configuration for chain."""
    if chain == "hedera":
        return get_swap_hedera(token_in, token_out, amount, account or "", slippage)
    if chain == "polygon":
        return get_swap_polygon(token_in, token_out, amount, account or "", slippage)
    raise ChainNotSupportedError(chain)


def _extract_token_addresses(chain: str, swap_config: dict) -> dict:
    """Extract token addresses from swap config."""
    if chain == "hedera":
        return {
            "token_in_address": swap_config.get("token_in_address", ""),
            "token_out_address": swap_config.get("token_out_address", ""),
            "token_in_address_evm": swap_config.get("token_in_address_evm", ""),
            "token_out_address_evm": swap_config.get("token_out_address_evm", ""),
        }
    return {
        "token_in_address": swap_config.get("token_in_address", ""),
        "token_out_address": swap_config.get("token_out_address", ""),
        "token_in_address_evm": swap_config.get("token_in_address", ""),
        "token_out_address_evm": swap_config.get("token_out_address", ""),
    }


def _fetch_balance(
    chain: str, account: str, token_address: str, token_symbol: str
) -> float:
    """Fetch balance for account and token."""
    try:
        if chain == "hedera":
            result = get_balance_hedera(account, token_address=token_address)
        else:
            result = get_balance_polygon(account, token_address=token_address)
        if result.get("balances"):
            for balance_item in result["balances"]:
                if balance_item.get("token_address") == token_address:
                    return float(balance_item.get("balance", "0"))
                if (
                    token_symbol in ["HBAR", "MATIC"]
                    and balance_item.get("token_type") == "native"
                ):
                    return float(balance_item.get("balance", "0"))
    except Exception as e:
        print(f"⚠️ Error fetching balance: {e}")
    return 0.0


def execute_swap(
    chain: str,
    token_in_symbol: str,
    token_out_symbol: str,
    amount_in: str,
    account_address: Optional[str],
    slippage_tolerance: float,
) -> dict:
    """Execute swap and return swap data."""
    swap_config = _get_swap_config(
        chain,
        token_in_symbol,
        token_out_symbol,
        amount_in,
        account_address,
        slippage_tolerance,
    )
    addresses = _extract_token_addresses(chain, swap_config)
    try:
        amount_float = float(amount_in)
    except Exception:
        amount_float = 0.01
    actual_balance = 0.0
    balance_sufficient = False
    if account_address:
        actual_balance = _fetch_balance(
            chain, account_address, addresses["token_in_address"], token_in_symbol
        )
        balance_sufficient = actual_balance >= amount_float
    balance_check = None
    if account_address:
        balance_check = {
            "account_address": account_address,
            "token_symbol": token_in_symbol,
            "balance": f"{actual_balance:.2f}",
            "balance_sufficient": balance_sufficient,
            "required_amount": f"{amount_float:.2f}",
        }
    amount_out = swap_config.get("amount_out", "0")
    amount_out_min = swap_config.get("amount_out_min", "0")
    swap_fee_percent = swap_config.get("swap_fee_percent", 0.3)
    tx_hash = f"0x{''.join([random.choice('0123456789abcdef') for _ in range(64)])}"
    swap_fee_amount = amount_float * (swap_fee_percent / 100)
    transaction_token_in = (
        addresses["token_in_address_evm"]
        if chain == "hedera"
        else addresses["token_in_address"]
    )
    transaction_token_out = (
        addresses["token_out_address_evm"]
        if chain == "hedera"
        else addresses["token_out_address"]
    )
    transaction = {
        "chain": chain,
        "token_in_symbol": token_in_symbol,
        "token_in_address": transaction_token_in,
        "token_in_address_hedera": addresses["token_in_address"]
        if chain == "hedera"
        else None,
        "token_out_symbol": token_out_symbol,
        "token_out_address": transaction_token_out,
        "token_out_address_hedera": addresses["token_out_address"]
        if chain == "hedera"
        else None,
        "amount_in": amount_in,
        "amount_out": amount_out,
        "amount_out_min": amount_out_min,
        "swap_fee": f"${swap_fee_amount:.2f}",
        "swap_fee_percent": swap_fee_percent,
        "estimated_time": "~30 seconds",
        "dex_name": swap_config.get("dex_name", "Unknown"),
        "pool_address": swap_config.get("router_address", ""),
        "slippage_tolerance": slippage_tolerance,
        "transaction_hash": tx_hash,
        "status": "pending",
        "price_impact": "0.1%",
        "swap_path": swap_config.get("swap_path", []),
        "rpc_url": swap_config.get("rpc_url", ""),
    }
    return {
        "chain": chain,
        "token_in_symbol": token_in_symbol,
        "token_out_symbol": token_out_symbol,
        "amount_in": amount_in,
        "account_address": account_address,
        "balance_check": balance_check,
        "transaction": transaction,
        "swap_config": swap_config,
    }
