"""
CoinGecko API tools for fetching market insights data.
"""

import requests
from typing import Optional, Dict, Any, List
from google.genai.types import FunctionDeclaration
from ..core.constants import (
    get_coingecko_api_key,
    get_coingecko_onchain_api_base,
    get_coingecko_api_header_name,
    get_coingecko_api_param_name,
    SUPPORTED_NETWORKS,
)
from ..core.exceptions import (
    CoinGeckoAPIError,
    NetworkNotSupportedError,
)


def _make_api_request(
    endpoint: str, params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make a request to CoinGecko API (Demo API)."""
    api_key = get_coingecko_api_key()
    if not api_key:
        raise CoinGeckoAPIError("CoinGecko API key not configured")

    # Use Demo API base URL and header/param names
    api_base = get_coingecko_onchain_api_base()
    header_name = get_coingecko_api_header_name()
    param_name = get_coingecko_api_param_name()

    # Log API being used (only once per session)
    if not hasattr(_make_api_request, "_logged_api_type"):
        print(f"🔑 Using CoinGecko Demo API: {api_base}")
        _make_api_request._logged_api_type = True

    url = f"{api_base}/{endpoint}"
    headers = {header_name: api_key}

    if params:
        params[param_name] = api_key
    else:
        params = {param_name: api_key}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        # Try to get error details from response
        error_details = ""
        try:
            error_details = response.json()
        except:
            error_details = response.text[:500]
        raise CoinGeckoAPIError(
            f"API request failed: {str(e)}. URL: {url}. Response: {error_details}"
        )
    except requests.exceptions.RequestException as e:
        raise CoinGeckoAPIError(f"API request failed: {str(e)}")


def get_pool_data(network: str, pool_address: str) -> Dict[str, Any]:
    """
    Get comprehensive pool data including liquidity, volume, and price.

    Args:
        network: Network ID (eth, polygon, hedera)
        pool_address: Pool contract address

    Returns:
        Dictionary with pool data including liquidity, volume, and price
    """
    if network not in SUPPORTED_NETWORKS:
        raise NetworkNotSupportedError(
            f"Network {network} not supported. Supported: {SUPPORTED_NETWORKS}"
        )

    endpoint = f"networks/{network}/pools/{pool_address}"
    return _make_api_request(endpoint)


def get_token_data(network: str, token_address: str) -> Dict[str, Any]:
    """
    Get comprehensive token data including price, volume, and liquidity.

    Args:
        network: Network ID (eth, polygon, hedera)
        token_address: Token contract address

    Returns:
        Dictionary with token data including price, volume, and liquidity
    """
    if network not in SUPPORTED_NETWORKS:
        raise NetworkNotSupportedError(
            f"Network {network} not supported. Supported: {SUPPORTED_NETWORKS}"
        )

    endpoint = f"networks/{network}/tokens/{token_address}"
    params = {"include": "top_pools"}
    return _make_api_request(endpoint, params)


def get_token_top_pools(network: str, token_address: str) -> Dict[str, Any]:
    """
    Get top pools for a token with liquidity and volume data.

    Args:
        network: Network ID (eth, polygon, hedera)
        token_address: Token contract address

    Returns:
        Dictionary with top pools data
    """
    if network not in SUPPORTED_NETWORKS:
        raise NetworkNotSupportedError(
            f"Network {network} not supported. Supported: {SUPPORTED_NETWORKS}"
        )

    endpoint = f"networks/{network}/tokens/{token_address}/pools"
    return _make_api_request(endpoint)


def get_trending_pools(
    network: Optional[str] = None, duration: str = "24h"
) -> Dict[str, Any]:
    """
    Get trending pools on a network or across all networks.

    Args:
        network: Optional network ID (eth, polygon, hedera). If None, returns trending across all networks.
        duration: Duration for trending (5m, 1h, 6h, 24h). Default is 24h.
                  Note: Duration parameter may not be supported in demo API.

    Returns:
        Dictionary with trending pools data
    """
    if network:
        if network not in SUPPORTED_NETWORKS:
            raise NetworkNotSupportedError(
                f"Network {network} not supported. Supported: {SUPPORTED_NETWORKS}"
            )
        # Use the correct endpoint format: /networks/{network}/trending_pools
        endpoint = f"networks/{network}/trending_pools"
        # Try without duration first (demo API may not support it)
        params = {"page": 1}
    else:
        # For all networks, use /networks/trending_pools
        endpoint = "networks/trending_pools"
        params = {"page": 1}

    return _make_api_request(endpoint, params)


def get_token_price(network: str, token_address: str) -> Dict[str, Any]:
    """
    Get token price using the simple price endpoint (available in demo API).

    Args:
        network: Network ID (eth, polygon, hedera)
        token_address: Token contract address

    Returns:
        Dictionary with token price data
    """
    if network not in SUPPORTED_NETWORKS:
        raise NetworkNotSupportedError(
            f"Network {network} not supported. Supported: {SUPPORTED_NETWORKS}"
        )

    # Use simple price endpoint: /simple/networks/{network}/token_price/{addresses}
    endpoint = f"simple/networks/{network}/token_price/{token_address}"
    return _make_api_request(endpoint)


def get_trending_search_pools() -> Dict[str, Any]:
    """
    Get trending pools based on search activity across all networks.

    NOTE: This endpoint requires Analyst plan or above (paid plan).
    For demo/free tier, use get_trending_pools() instead.

    Returns:
        Dictionary with trending search pools data
    """
    # Use the search pools endpoint: /pools/trending_search
    # This requires paid plan - will return 401 with demo API
    endpoint = "pools/trending_search"
    return _make_api_request(endpoint)


# ADK Function Declarations for LLM tool calling
def _get_pool_data_declaration() -> FunctionDeclaration:
    """Get function declaration for get_pool_data."""
    return FunctionDeclaration(
        name="get_pool_data",
        description="Get comprehensive pool data including liquidity (reserve_in_usd), volume (24h), and price for a specific pool on a network",
        parameters={
            "type": "object",
            "properties": {
                "network": {
                    "type": "string",
                    "enum": ["eth", "polygon", "hedera"],
                    "description": "Network ID: eth for Ethereum, polygon for Polygon, hedera for Hedera",
                },
                "pool_address": {
                    "type": "string",
                    "description": "Pool contract address",
                },
            },
            "required": ["network", "pool_address"],
        },
    )


def _get_token_data_declaration() -> FunctionDeclaration:
    """Get function declaration for get_token_data."""
    return FunctionDeclaration(
        name="get_token_data",
        description="Get comprehensive token data including real-time price, 24-hour volume, and total liquidity across all pools for a token",
        parameters={
            "type": "object",
            "properties": {
                "network": {
                    "type": "string",
                    "enum": ["eth", "polygon", "hedera"],
                    "description": "Network ID: eth for Ethereum, polygon for Polygon, hedera for Hedera",
                },
                "token_address": {
                    "type": "string",
                    "description": "Token contract address",
                },
            },
            "required": ["network", "token_address"],
        },
    )


def _get_token_top_pools_declaration() -> FunctionDeclaration:
    """Get function declaration for get_token_top_pools."""
    return FunctionDeclaration(
        name="get_token_top_pools",
        description="Get top pools for a token with liquidity and volume data across multiple pools",
        parameters={
            "type": "object",
            "properties": {
                "network": {
                    "type": "string",
                    "enum": ["eth", "polygon", "hedera"],
                    "description": "Network ID: eth for Ethereum, polygon for Polygon, hedera for Hedera",
                },
                "token_address": {
                    "type": "string",
                    "description": "Token contract address",
                },
            },
            "required": ["network", "token_address"],
        },
    )


def _get_trending_pools_declaration() -> FunctionDeclaration:
    """Get function declaration for get_trending_pools."""
    return FunctionDeclaration(
        name="get_trending_pools",
        description="Get trending pools on a network or across all networks based on trading activity",
        parameters={
            "type": "object",
            "properties": {
                "network": {
                    "type": "string",
                    "enum": ["eth", "polygon", "hedera"],
                    "description": "Optional network ID. If not provided, returns trending across all networks",
                },
            },
            "required": [],
        },
    )


def _get_trending_search_pools_declaration() -> FunctionDeclaration:
    """Get function declaration for get_trending_search_pools."""
    return FunctionDeclaration(
        name="get_trending_search_pools",
        description="Get trending pools based on search activity across all networks. Returns trending token addresses and pools",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )


# Export tools for ADK - these are the actual functions that ADK will use
# ADK automatically converts Python functions to tools based on their signatures
def get_agent_tools() -> List:
    """Get list of tools for the agent."""
    return [
        get_pool_data,
        get_token_data,
        get_token_top_pools,
        get_token_price,  # Simple price endpoint (demo API compatible)
        get_trending_pools,
        # get_trending_search_pools,  # Removed - requires paid plan
    ]
