"""
Tools for extracting swap parameters using LLM with structured data.
"""

from lib.shared.blockchain.tokens import (  # noqa: E402
    get_token_address,
    CHAIN_TOKENS,
)


def get_token_address_for_chain(
    chain: str, token_symbol: str, use_evm: bool = False
) -> dict:
    """Get token address for a given chain and token symbol.

    This tool helps extract token addresses from token symbols.
    Use this when you need to look up the address for a token symbol.

    Args:
        chain: Chain name (hedera or polygon)
        token_symbol: Token symbol (e.g., HBAR, USDC, USDT, MATIC, ETH, etc.)
        use_evm: If True and chain is hedera, return EVM address for contract calls.
                 If False, return Hedera format address for balance checking.
                 For Polygon, this parameter is ignored (always EVM format).

    Returns:
        Dictionary with token address information:
        {
            "token_symbol": "USDC",
            "chain": "hedera",
            "address_hedera": "0.0.456858",  # Hedera format (for balance checking)
            "address_evm": "0x000000000000000000000000000000000006f89a",  # EVM format (for contracts)
            "found": true
        }
    """
    chain_lower = chain.lower()
    token_symbol_upper = token_symbol.upper()

    # Check if token exists on this chain
    if chain_lower not in CHAIN_TOKENS:
        return {
            "token_symbol": token_symbol_upper,
            "chain": chain_lower,
            "address_hedera": "",
            "address_evm": "",
            "found": False,
            "error": f"Chain {chain_lower} not supported",
        }

    tokens = CHAIN_TOKENS[chain_lower]
    if token_symbol_upper not in tokens:
        return {
            "token_symbol": token_symbol_upper,
            "chain": chain_lower,
            "address_hedera": "",
            "address_evm": "",
            "found": False,
            "error": f"Token {token_symbol_upper} not found on {chain_lower}",
        }

    # Get addresses
    address_hedera = get_token_address(chain_lower, token_symbol_upper, use_evm=False)
    address_evm = get_token_address(chain_lower, token_symbol_upper, use_evm=True)

    return {
        "token_symbol": token_symbol_upper,
        "chain": chain_lower,
        "address_hedera": address_hedera,
        "address_evm": address_evm,
        "found": True,
    }


def get_available_tokens_for_chain(chain: str) -> dict:
    """Get list of available tokens for a given chain.

    Use this tool to see what tokens are available on a specific chain.

    Args:
        chain: Chain name (hedera or polygon)

    Returns:
        Dictionary with list of available tokens:
        {
            "chain": "hedera",
            "tokens": ["HBAR", "USDC", "USDT", "ETH", "SAUCE", "LINK", "AVAX", ...]
        }
    """
    chain_lower = chain.lower()

    if chain_lower not in CHAIN_TOKENS:
        return {
            "chain": chain_lower,
            "tokens": [],
            "error": f"Chain {chain_lower} not supported",
        }

    tokens = list(CHAIN_TOKENS[chain_lower].keys())

    return {"chain": chain_lower, "tokens": tokens}
