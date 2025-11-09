"""
Polygon-specific swap functionality.
"""

from typing import Optional, Dict, Any
from .constants import get_token_address, get_dex_config, get_chain_rpc_url


def get_swap_polygon(
    token_in_symbol: str,
    token_out_symbol: str,
    amount_in: str,
    account_address: str,
    slippage_tolerance: float = 0.5,
    dex_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get swap configuration for Polygon chain.

    Args:
        token_in_symbol: Token symbol to swap from (e.g., "MATIC", "USDC")
        token_out_symbol: Token symbol to swap to (e.g., "USDC", "MATIC")
        amount_in: Amount to swap (human-readable format)
        account_address: Account address for the swap
        slippage_tolerance: Slippage tolerance percentage (default: 0.5)
        dex_name: Optional DEX name (default: uses default DEX for chain)

    Returns:
        Dictionary with swap configuration including addresses, paths, etc.
    """
    # Get token addresses
    token_in_address = get_token_address("polygon", token_in_symbol)
    token_out_address = get_token_address("polygon", token_out_symbol)

    # Get DEX configuration
    dex_config = get_dex_config("polygon", dex_name)
    dex_name_actual = dex_config.get("name", "QuickSwap")
    router_address = dex_config.get(
        "router_address", "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"
    )

    # Calculate swap path
    # For Polygon, direct path for most swaps
    swap_path = []

    if token_in_symbol == "MATIC":
        # Native MATIC swap: MATIC -> WMATIC -> Token
        wmatic_address = get_token_address("polygon", "WMATIC")
        if wmatic_address:
            swap_path.append(wmatic_address)
        swap_path.append(token_out_address)
    elif token_out_symbol == "MATIC":
        # Token -> WMATIC -> MATIC
        swap_path.append(token_in_address)
        wmatic_address = get_token_address("polygon", "WMATIC")
        if wmatic_address:
            swap_path.append(wmatic_address)
    else:
        # Token -> Token (direct path)
        swap_path.append(token_in_address)
        swap_path.append(token_out_address)

    # Calculate estimated output (mock for now - in production, query DEX pools)
    try:
        amount_float = float(amount_in)
    except (ValueError, TypeError):
        amount_float = 0.01

    # Simple estimation: 0.5% fee
    amount_out_float = amount_float * 0.995
    amount_out_min_float = amount_out_float * (1 - slippage_tolerance / 100)

    return {
        "chain": "polygon",
        "token_in_symbol": token_in_symbol,
        "token_in_address": token_in_address,
        "token_out_symbol": token_out_symbol,
        "token_out_address": token_out_address,
        "amount_in": amount_in,
        "amount_out": f"{amount_out_float:.6f}",
        "amount_out_min": f"{amount_out_min_float:.6f}",
        "swap_path": swap_path,
        "dex_name": dex_name_actual,
        "router_address": router_address,
        "slippage_tolerance": slippage_tolerance,
        "swap_fee_percent": dex_config.get("default_fee_percent", 0.3),
        "rpc_url": get_chain_rpc_url("polygon"),
    }
