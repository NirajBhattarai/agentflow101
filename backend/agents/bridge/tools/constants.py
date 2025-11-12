"""
Constants and utilities for bridge tools.
"""

from typing import Optional, Dict, Any
from lib.shared.blockchain.tokens import get_token_address


def get_token_address_for_chain(
    chain: str, token_symbol: str, use_evm: bool = True
) -> str:
    """
    Get token address for a chain.
    
    Args:
        chain: Chain name (hedera, polygon)
        token_symbol: Token symbol (USDC, USDT, etc.)
        use_evm: Whether to use EVM address (for Hedera)
    
    Returns:
        Token address
    """
    try:
        return get_token_address(chain, token_symbol, use_evm=use_evm)
    except Exception as e:
        print(f"⚠️ Error getting token address: {e}")
        return ""


def get_available_tokens_for_chain(chain: str) -> list:
    """
    Get available tokens for a chain.
    
    Args:
        chain: Chain name (hedera, polygon)
    
    Returns:
        List of token symbols
    """
    from lib.shared.blockchain.tokens import CHAIN_TOKENS
    
    return list(CHAIN_TOKENS.get(chain, {}).keys())

