"""
Constants file containing token addresses and pool addresses for different chains.
This serves as a registry for looking up addresses when fetching liquidity data.
"""

# Polygon
POLYGON_TOKENS = {
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
}

POLYGON_POOLS = {
    "USDC-MATIC": {
        "quickswap": "0x6e7a5FAFcec6BB1e78bAE2A1F0B6121BF5779D35",
    },
    "USDC-USDT": {
        "quickswap": "0x6e7a5FAFcec6BB1e78bAE2A1F0B6121BF5779D35",
    },
}

# Hedera
HEDERA_TOKENS = {
    "USDC": "0.0.456858",
    "HBAR": "0.0.0",  # Native token
    "WHBAR": "0.0.1456986",  # Wrapped HBAR token
}

HEDERA_POOLS = {
    "USDC-HBAR": {
        "saucerswap": "0.0.123456",
        "heliswap": "0.0.789012",
        "silksuite": "0.0.345678",
    },
    "USDC-USDT": {
        "saucerswap": "0.0.234567",
    },
}

# Chain-specific mappings for easy lookup
CHAIN_TOKENS = {
    "polygon": POLYGON_TOKENS,
    "hedera": HEDERA_TOKENS,
}

CHAIN_POOLS = {
    "polygon": POLYGON_POOLS,
    "hedera": HEDERA_POOLS,
}


# Helper function to get token address
def get_token_address(chain: str, token_symbol: str) -> str:
    """Get token address for a given chain and token symbol."""
    chain_lower = chain.lower()
    if chain_lower in CHAIN_TOKENS:
        tokens = CHAIN_TOKENS[chain_lower]
        return tokens.get(token_symbol.upper(), "")
    return ""


# Helper function to get pool address
def get_pool_address(chain: str, pair: str, dex: str = None) -> str:
    """Get pool address for a given chain, token pair, and optionally DEX."""
    chain_lower = chain.lower()
    if chain_lower in CHAIN_POOLS:
        pools = CHAIN_POOLS[chain_lower]
        if pair in pools:
            if dex:
                return pools[pair].get(dex.lower(), "")
            # Return first available pool if DEX not specified
            return list(pools[pair].values())[0] if pools[pair] else ""
    return ""
