"""
Constants file containing token addresses for balance checking.
Uses the same token mappings as liquidity tools for consistency.
"""

# Polygon
POLYGON_TOKENS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
}

# Hedera
HEDERA_TOKENS = {
    "USDC": "0.0.456858",
    "HBAR": "0.0.0",  # Native token
    "WHBAR": "0.0.1456986",  # Wrapped HBAR token
}

# Chain-specific mappings for easy lookup
CHAIN_TOKENS = {
    "polygon": POLYGON_TOKENS,
    "hedera": HEDERA_TOKENS,
}


# Helper function to get token address
def get_token_address(chain: str, token_symbol: str) -> str:
    """Get token address for a given chain and token symbol."""
    chain_lower = chain.lower()
    if chain_lower in CHAIN_TOKENS:
        tokens = CHAIN_TOKENS[chain_lower]
        return tokens.get(token_symbol.upper(), "")
    return ""
