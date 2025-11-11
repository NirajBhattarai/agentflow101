"""
Hedera-specific swap functionality.
"""

from typing import Optional, Dict, Any
from lib.shared.blockchain.tokens import get_token_address  # noqa: E402
from lib.shared.blockchain.dex import get_dex_config  # noqa: E402
from lib.shared.blockchain.networks import get_chain_rpc_url  # noqa: E402


def get_swap_hedera(
    token_in_symbol: str,
    token_out_symbol: str,
    amount_in: str,
    account_address: str,
    slippage_tolerance: float = 0.5,
    dex_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get swap configuration for Hedera chain.

    Args:
        token_in_symbol: Token symbol to swap from (e.g., "HBAR", "USDC")
        token_out_symbol: Token symbol to swap to (e.g., "USDC", "HBAR")
        amount_in: Amount to swap (human-readable format)
        account_address: Account address for the swap
        slippage_tolerance: Slippage tolerance percentage (default: 0.5)
        dex_name: Optional DEX name (default: uses default DEX for chain)

    Returns:
        Dictionary with swap configuration including addresses, paths, etc.
    """
    # Get token addresses (Hedera format for balance checking)
    token_in_address_hedera = get_token_address(
        "hedera", token_in_symbol, use_evm=False
    )
    token_out_address_hedera = get_token_address(
        "hedera", token_out_symbol, use_evm=False
    )

    # Get EVM addresses (for contract calls)
    token_in_address_evm = get_token_address("hedera", token_in_symbol, use_evm=True)
    token_out_address_evm = get_token_address("hedera", token_out_symbol, use_evm=True)

    # Get DEX configuration
    dex_config = get_dex_config("hedera", dex_name)
    dex_name_actual = dex_config.get("name", "SaucerSwap")
    router_address = dex_config.get(
        "router_address", "0x00000000000000000000000000000000006715e6"
    )

    # Calculate swap path (use EVM addresses for contract calls)
    # For Hedera, common path is WHBAR -> Token (for native HBAR swaps)
    swap_path_evm = []

    if token_in_symbol == "HBAR":
        # Native HBAR swap: HBAR -> WHBAR -> Token
        whbar_address_evm = get_token_address("hedera", "WHBAR", use_evm=True)
        if whbar_address_evm:
            swap_path_evm.append(whbar_address_evm)
        swap_path_evm.append(token_out_address_evm)
    elif token_out_symbol == "HBAR":
        # Token -> WHBAR -> HBAR
        swap_path_evm.append(token_in_address_evm)
        whbar_address_evm = get_token_address("hedera", "WHBAR", use_evm=True)
        if whbar_address_evm:
            swap_path_evm.append(whbar_address_evm)
    else:
        # Token -> Token (may need intermediate path)
        swap_path_evm.append(token_in_address_evm)
        swap_path_evm.append(token_out_address_evm)

    # Calculate estimated output (mock for now - in production, query DEX pools)
    try:
        amount_float = float(amount_in)
    except (ValueError, TypeError):
        amount_float = 0.01

    # Simple estimation: 0.5% fee
    amount_out_float = amount_float * 0.995
    amount_out_min_float = amount_out_float * (1 - slippage_tolerance / 100)

    return {
        "chain": "hedera",
        "token_in_symbol": token_in_symbol,
        "token_in_address": token_in_address_hedera,  # Hedera format for balance checking
        "token_in_address_evm": token_in_address_evm,  # EVM format for contract calls
        "token_out_symbol": token_out_symbol,
        "token_out_address": token_out_address_hedera,  # Hedera format for balance checking
        "token_out_address_evm": token_out_address_evm,  # EVM format for contract calls
        "amount_in": amount_in,
        "amount_out": f"{amount_out_float:.6f}",
        "amount_out_min": f"{amount_out_min_float:.6f}",
        "swap_path": swap_path_evm,  # EVM addresses for contract calls
        "swap_path_hedera": [
            token_in_address_hedera,
            token_out_address_hedera,
        ],  # Hedera format for reference
        "dex_name": dex_name_actual,
        "router_address": router_address,
        "router_address_hedera": dex_config.get("router_address_hedera"),
        "slippage_tolerance": slippage_tolerance,
        "swap_fee_percent": dex_config.get("default_fee_percent", 0.3),
        "rpc_url": get_chain_rpc_url("hedera"),
    }
