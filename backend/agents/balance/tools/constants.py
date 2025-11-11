"""
Constants file containing token addresses for balance checking.
Uses the same token mappings as liquidity tools for consistency.
"""

# Polygon
POLYGON_TOKENS = {
    "MATIC": "0x0000000000000000000000000000000000001010",
    "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    "POL": "0x0000000000000000000000000000000000001010",
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    "AAVE": "0x8dff5e27eaac0e4460d4a3e9bf9a3e3181077410",
    "LINK": "0x53e0bca35ec356bd5dddfebbd1fc0fd03fabad39",
    "QUICK": "0x831753dd7087cac61ab5644b308642cc1c33dc13",
    "SAND": "0xbbba073c31bf03b8acf7c28ef0738decf3695683",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
}

# Hedera
# Use Hedera format addresses (0.0.123456) for balance checking via Mirror Node API
HEDERA_TOKENS = {
    "HBAR": "0.0.0",  # Native token
    "SAUCE": "0.0.731861",  # SaucerSwap Token
    "USDC": "0.0.456858",  # USD Coin
    "JAM": "0.0.127877",  # Tune.FM
    "DOV": "0.0.624505",  # Dovu
    "HBARX": "0.0.803264",  # Stader Labs
    "SHIBR": "0.0.751086",  # Shibar
    "SKUX": "0.0.485527",  # SKUx (Note: user provided 0.0485527, corrected to 0.0.485527)
    "TNG": "0.0.795239",  # Tangent Finance
    "HTC": "0.0.796381",  # Hippocratic Token
    "USDT": "0.0.1055472",
    "WHBAR": "0.0.1456986",  # Wrapped HBAR token
    "ETH": "0.0.541564",  # Wrapped Ethereum
    "WETH": "0.0.541564",  # Wrapped Ethereum (same as ETH)
    "BTC": "0.0.1055483",  # Wrapped Bitcoin
    "LINK": "0.0.1055495",  # Chainlink
    "AVAX": "0.0.1157020",  # Avalanche
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
