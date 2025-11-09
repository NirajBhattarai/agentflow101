"""
Constants file containing chain-specific configurations for swaps.
Organized to easily add new chains in the future.
"""

# Token addresses by chain
# Polygon tokens - comprehensive list
POLYGON_TOKENS = {
    "MATIC": "0x0000000000000000000000000000000000000000",  # Native token
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    "ETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "WBTC": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",  # Wrapped ETH (same as ETH on Polygon)
    "LINK": "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad99",  # Chainlink
    "AAVE": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",  # Aave Token
    "UNI": "0xb33EaAd8d922B1083446DC23f610c2567fB5180f",  # Uniswap
    "CRV": "0x172370d5Cd63279eFa6d502DAB29171933a610AF",  # Curve DAO Token
}

# Hedera tokens - comprehensive list
# Format: Hedera address (for balance checking) -> EVM address (for contract calls)
HEDERA_TOKENS = {
    "HBAR": "0.0.0",  # Native token
    "USDC": "0.0.456858",
    "USDT": "0.0.1055472",
    "WHBAR": "0.0.1456986",  # Wrapped HBAR token
    "ETH": "0.0.541564",  # Wrapped Ethereum
    "WETH": "0.0.541564",  # Wrapped Ethereum (same as ETH)
    "BTC": "0.0.1055483",  # Wrapped Bitcoin
    "SAUCE": "0.0.731861",  # SaucerSwap Token
    "LINK": "0.0.1055495",  # Chainlink
    "AVAX": "0.0.1157020",  # Avalanche
}

# Hedera token EVM address mapping
# Used when calling smart contracts (Hedera uses EVM addresses for contracts)
# Format: Hedera address (0.0.123456) -> EVM address (0x...)
HEDERA_TOKEN_EVM_ADDRESSES = {
    "HBAR": "0x0000000000000000000000000000000000000000",  # Native token (0.0.0)
    "USDC": "0x000000000000000000000000000000000006f89a",  # 0.0.456858 -> EVM
    "USDT": "0x0000000000000000000000000000000000101b07",  # 0.0.1055472 -> EVM (placeholder, update if needed)
    "WHBAR": "0x0000000000000000000000000000000000163B5a",  # 0.0.1456986 -> EVM (placeholder, update if needed)
    "ETH": "0x000000000000000000000000000000000008437c",  # 0.0.541564 -> EVM
    "WETH": "0x000000000000000000000000000000000008437c",  # Same as ETH (0.0.541564)
    "BTC": "0x0000000000000000000000000000000000101b07",  # 0.0.1055483 -> EVM (placeholder, update if needed)
    "SAUCE": "0x00000000000000000000000000000000000b2ad5",  # 0.0.731861 -> EVM
    "LINK": "0x0000000000000000000000000000000000101b07",  # 0.0.1055495 -> EVM (note: same as USDT placeholder, verify)
    "AVAX": "0x000000000000000000000000000000000011a79c",  # 0.0.1157020 -> EVM
}

# Chain-specific token mappings
CHAIN_TOKENS = {
    "polygon": POLYGON_TOKENS,
    "hedera": HEDERA_TOKENS,
}

# DEX configurations by chain
POLYGON_DEX_CONFIG = {
    "quickswap": {
        "name": "QuickSwap",
        "router_address": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",  # QuickSwap Router V2
        "factory_address": "0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32",
        "default_fee_percent": 0.3,
    },
    "uniswap": {
        "name": "Uniswap V3",
        "router_address": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "factory_address": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "default_fee_percent": 0.3,
    },
}

HEDERA_DEX_CONFIG = {
    "saucerswap": {
        "name": "SaucerSwap",
        "router_address": "0x00000000000000000000000000000000006715e6",  # Mainnet router EVM address
        "router_address_hedera": "0.0.6755814",  # Mainnet router Hedera address
        "factory_address": "0x0000000000000000000000000000000000000000",  # TODO: Add actual factory
        "default_fee_percent": 0.3,
    },
    "heliswap": {
        "name": "HeliSwap",
        "router_address": "0x0000000000000000000000000000000000000000",  # TODO: Add actual router
        "factory_address": "0x0000000000000000000000000000000000000000",  # TODO: Add actual factory
        "default_fee_percent": 0.3,
    },
}

# Chain-specific DEX configurations
CHAIN_DEX_CONFIG = {
    "polygon": POLYGON_DEX_CONFIG,
    "hedera": HEDERA_DEX_CONFIG,
}

# Default DEX by chain
DEFAULT_DEX = {
    "polygon": "quickswap",
    "hedera": "saucerswap",
}

# RPC URLs by chain
RPC_URLS = {
    "polygon": {
        "mainnet": "https://polygon-rpc.com",
        "testnet": "https://rpc-mumbai.maticvigil.com",
    },
    "hedera": {
        "mainnet": "https://mainnet.hashio.io/api",
        "testnet": "https://testnet.hashio.io/api",
    },
}

# Explorer URLs by chain
EXPLORER_URLS = {
    "polygon": {
        "mainnet": "https://polygonscan.com",
        "testnet": "https://mumbai.polygonscan.com",
    },
    "hedera": {
        "mainnet": "https://hashscan.io/mainnet",
        "testnet": "https://hashscan.io/testnet",
    },
}


def get_token_address(chain: str, token_symbol: str, use_evm: bool = False) -> str:
    """Get token address for a given chain and token symbol.

    Args:
        chain: Chain name (hedera, polygon, etc.)
        token_symbol: Token symbol (HBAR, USDC, etc.)
        use_evm: If True and chain is hedera, return EVM address.
                 For balance checking, use False (Hedera format).
                 For contract calls, use True (EVM format).

    Returns:
        Token address in appropriate format
    """
    # Validate inputs
    if not token_symbol:
        raise ValueError("Token symbol is required and cannot be None or empty")

    chain_lower = chain.lower()
    token_symbol_upper = token_symbol.upper()

    if chain_lower == "hedera" and use_evm:
        # Return EVM address for Hedera contract calls
        return HEDERA_TOKEN_EVM_ADDRESSES.get(token_symbol_upper, "")
    elif chain_lower in CHAIN_TOKENS:
        tokens = CHAIN_TOKENS[chain_lower]
        return tokens.get(token_symbol_upper, "")

    return ""


def hedera_to_evm_address(hedera_address: str) -> str:
    """Convert Hedera address (0.0.123456) to EVM address (0x...).

    Args:
        hedera_address: Hedera format address (e.g., "0.0.456858")

    Returns:
        EVM format address (e.g., "0x000000000000000000000000000000000006f89a")
    """
    import re

    # Check if already EVM format
    if hedera_address.startswith("0x"):
        return hedera_address

    # Check if it's a known token
    for symbol, hedera_addr in HEDERA_TOKENS.items():
        if hedera_addr == hedera_address:
            evm_addr = HEDERA_TOKEN_EVM_ADDRESSES.get(symbol)
            if evm_addr:
                return evm_addr

    # Convert Hedera account ID to EVM address
    # Format: 0.0.123456 -> extract 123456 -> convert to hex -> pad to 40 chars
    match = re.match(r"^0\.0\.(\d+)$", hedera_address)
    if match:
        account_num = int(match.group(1))
        hex_str = hex(account_num)[2:].lower()
        # Pad to 40 hex characters (20 bytes)
        hex_padded = hex_str.zfill(40)
        return f"0x{hex_padded}"

    return hedera_address  # Return as-is if conversion fails


def get_dex_config(chain: str, dex_name: str = None) -> dict:
    """Get DEX configuration for a given chain and optional DEX name."""
    chain_lower = chain.lower()
    if chain_lower not in CHAIN_DEX_CONFIG:
        return {}

    dex_configs = CHAIN_DEX_CONFIG[chain_lower]

    if dex_name:
        dex_lower = dex_name.lower()
        # Try to find matching DEX
        for key, config in dex_configs.items():
            if key.lower() == dex_lower or config["name"].lower() == dex_lower:
                return config
        return {}

    # Return default DEX if no name specified
    default_dex = DEFAULT_DEX.get(chain_lower)
    if default_dex and default_dex in dex_configs:
        return dex_configs[default_dex]

    # Return first available DEX as fallback
    if dex_configs:
        return list(dex_configs.values())[0]

    return {}


def get_chain_rpc_url(chain: str, network: str = "mainnet") -> str:
    """Get RPC URL for a given chain and network."""
    chain_lower = chain.lower()
    network_lower = network.lower()

    if chain_lower in RPC_URLS and network_lower in RPC_URLS[chain_lower]:
        return RPC_URLS[chain_lower][network_lower]

    return ""


def get_explorer_url(chain: str, network: str = "mainnet") -> str:
    """Get explorer URL for a given chain and network."""
    chain_lower = chain.lower()
    network_lower = network.lower()

    if chain_lower in EXPLORER_URLS and network_lower in EXPLORER_URLS[chain_lower]:
        return EXPLORER_URLS[chain_lower][network_lower]

    return ""
