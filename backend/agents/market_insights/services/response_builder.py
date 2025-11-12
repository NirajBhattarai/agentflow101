"""
Response builder for Market Insights Agent.
"""

import json
from typing import Dict, Any, Optional, List
from ..core.models.insights import (
    MarketInsightsResponse,
    PoolLiquidityData,
    TokenLiquidityData,
    TrendingTokenData,
)


def _extract_pool_data(data: Dict[str, Any]) -> Optional[PoolLiquidityData]:
    """Extract pool liquidity data from CoinGecko API response."""
    try:
        if "data" in data and "attributes" in data["data"]:
            attrs = data["data"]["attributes"]
            return PoolLiquidityData(
                pool_address=attrs.get("address", ""),
                base_token_address=attrs.get("base_token", {}).get("address")
                if attrs.get("base_token")
                else None,
                quote_token_address=attrs.get("quote_token", {}).get("address")
                if attrs.get("quote_token")
                else None,
                reserve_in_usd=attrs.get("reserve_in_usd"),
                base_token_liquidity_usd=attrs.get("base_token", {}).get(
                    "liquidity_usd"
                )
                if attrs.get("base_token")
                else None,
                quote_token_liquidity_usd=attrs.get("quote_token", {}).get(
                    "liquidity_usd"
                )
                if attrs.get("quote_token")
                else None,
                volume_24h_usd=attrs.get("volume_usd", {}).get("h24")
                if isinstance(attrs.get("volume_usd"), dict)
                else attrs.get("volume_usd"),
                price_usd=attrs.get("price_usd"),
                price_change_24h=attrs.get("price_change_percentage", {}).get("h24")
                if isinstance(attrs.get("price_change_percentage"), dict)
                else attrs.get("price_change_percentage"),
            )
    except Exception as e:
        print(f"⚠️  Error extracting pool data: {e}")
    return None


def _extract_token_data(data: Dict[str, Any]) -> Optional[TokenLiquidityData]:
    """Extract token liquidity data from CoinGecko API response."""
    try:
        if "data" in data and "attributes" in data["data"]:
            attrs = data["data"]["attributes"]
            token_address = attrs.get("address", "")

            # Extract top pools
            top_pools = []
            if "included" in data:
                for item in data["included"]:
                    if item.get("type") == "pool" and "attributes" in item:
                        pool_attrs = item["attributes"]
                        top_pools.append(
                            PoolLiquidityData(
                                pool_address=pool_attrs.get("address", ""),
                                base_token_address=pool_attrs.get("base_token", {}).get(
                                    "address"
                                )
                                if pool_attrs.get("base_token")
                                else None,
                                quote_token_address=pool_attrs.get(
                                    "quote_token", {}
                                ).get("address")
                                if pool_attrs.get("quote_token")
                                else None,
                                reserve_in_usd=pool_attrs.get("reserve_in_usd"),
                                volume_24h_usd=pool_attrs.get("volume_usd", {}).get(
                                    "h24"
                                )
                                if isinstance(pool_attrs.get("volume_usd"), dict)
                                else pool_attrs.get("volume_usd"),
                                price_usd=pool_attrs.get("price_usd"),
                            )
                        )

            return TokenLiquidityData(
                token_address=token_address,
                total_reserve_in_usd=attrs.get("total_reserve_in_usd"),
                price_usd=attrs.get("price_usd"),
                volume_24h_usd=attrs.get("volume_usd", {}).get("h24")
                if isinstance(attrs.get("volume_usd"), dict)
                else attrs.get("volume_usd"),
                price_change_24h=attrs.get("price_change_percentage", {}).get("h24")
                if isinstance(attrs.get("price_change_percentage"), dict)
                else attrs.get("price_change_percentage"),
                top_pools=top_pools,
            )
    except Exception as e:
        print(f"⚠️  Error extracting token data: {e}")
    return None


def _extract_trending_data(data: Dict[str, Any]) -> List[TrendingTokenData]:
    """Extract trending tokens data from API response."""
    trending_tokens = []
    try:
        if "data" in data:
            for item in data["data"]:
                if "attributes" in item:
                    attrs = item["attributes"]
                    # Only extract token information (no pools)
                    if item.get("type") == "token":
                        token_address = attrs.get("address", "")
                        network = (
                            attrs.get("network_id") or attrs.get("network") or "unknown"
                        )

                        if token_address:
                            trending_tokens.append(
                                TrendingTokenData(
                                    token_address=token_address,
                                    pool_address=None,  # No pools, only tokens
                                    network=network,
                                    price_usd=attrs.get("price_usd"),
                                    volume_24h_usd=attrs.get("volume_usd", {}).get(
                                        "h24"
                                    )
                                    if isinstance(attrs.get("volume_usd"), dict)
                                    else attrs.get("volume_usd"),
                                    reserve_in_usd=attrs.get("total_reserve_in_usd")
                                    or attrs.get("reserve_in_usd"),
                                    price_change_24h=attrs.get(
                                        "price_change_percentage", {}
                                    ).get("h24")
                                    if isinstance(
                                        attrs.get("price_change_percentage"), dict
                                    )
                                    else attrs.get("price_change_percentage"),
                                )
                            )
    except Exception as e:
        print(f"⚠️  Error extracting trending data: {e}")
    return trending_tokens


def build_market_insights_response(
    network: Optional[str] = None,
    token_address: Optional[str] = None,
    pool_address: Optional[str] = None,
    pool_data: Optional[Dict[str, Any]] = None,
    token_data: Optional[Dict[str, Any]] = None,
    trending_data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> str:
    """Build market insights response from API data."""
    try:
        response = MarketInsightsResponse(
            type="market_insights",
            network=network,
            token_address=token_address,
            pool_address=pool_address,
            pool_liquidity=_extract_pool_data(pool_data) if pool_data else None,
            token_liquidity=_extract_token_data(token_data) if token_data else None,
            trending_tokens=_extract_trending_data(trending_data)
            if trending_data
            else [],
            price_usd=None,
            volume_24h_usd=None,
            error=error,
        )

        # Set price and volume from token or pool data
        if response.token_liquidity:
            response.price_usd = response.token_liquidity.price_usd
            response.volume_24h_usd = response.token_liquidity.volume_24h_usd
        elif response.pool_liquidity:
            response.price_usd = response.pool_liquidity.price_usd
            response.volume_24h_usd = response.pool_liquidity.volume_24h_usd

        return json.dumps(response.model_dump(exclude_none=True), indent=2)
    except Exception as e:
        print(f"❌ Error building response: {e}")
        import traceback

        traceback.print_exc()
        return json.dumps(
            {
                "type": "market_insights",
                "error": f"Error building response: {str(e)}",
            },
            indent=2,
        )


def build_error_response(error: str) -> str:
    """Build error response."""
    return json.dumps(
        {
            "type": "market_insights",
            "error": error,
        },
        indent=2,
    )
