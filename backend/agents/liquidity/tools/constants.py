"""
Constants file containing token addresses and pool addresses for different chains.
This serves as a registry for looking up addresses when fetching liquidity data.
"""

# Ethereum Mainnet
ETHEREUM_TOKENS = {
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
}

ETHEREUM_POOLS = {
    "USDC-ETH": {
        "uniswap_v3": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8",
        "sushiswap": "0x397FF1542f962076d0BFE58eA045FfA2d347ACa0",
    },
    "USDC-USDT": {
        "uniswap_v3": "0x3416cF6C708Da44DB2624D63ea0AAef7113527C6",
    },
    "USDC-DAI": {
        "uniswap_v3": "0x5777d92f208679DB4b9778590Fa3cAB3Ac9e2168",
    },
}

# Binance Smart Chain (BSC)
BSC_TOKENS = {
    "USDC": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
    "USDT": "0x55d398326f99059fF775485246999027B3197955",
    "BUSD": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
    "BNB": "0x0000000000000000000000000000000000000000",  # Native token
    "WBNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
}

BSC_POOLS = {
    "USDT-BNB": {
        "pancakeswap_v3": "0x133B3d95bAD5405d14d53473671200e5C8e3E112",
        "pancakeswap_v2": "0x58F876857a02D6762E0101bb5C46A8c1ED44Dc16",
    },
    "USDC-BNB": {
        "pancakeswap_v3": "0x133B3d95bAD5405d14d53473671200e5C8e3E112",
    },
}

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
    "USDT": "0.0.1234567",  # Example, replace with actual
    "SAUCE": "0.0.1234568",  # SaucerSwap token
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
    "ethereum": ETHEREUM_TOKENS,
    "bsc": BSC_TOKENS,
    "polygon": POLYGON_TOKENS,
    "hedera": HEDERA_TOKENS,
}

CHAIN_POOLS = {
    "ethereum": ETHEREUM_POOLS,
    "bsc": BSC_POOLS,
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

