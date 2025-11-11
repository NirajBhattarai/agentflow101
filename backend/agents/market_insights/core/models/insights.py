"""
Pydantic models for Market Insights data structures.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PoolLiquidityData(BaseModel):
    """Liquidity data for a single pool."""

    pool_address: str = Field(..., description="Pool contract address")
    base_token_address: Optional[str] = Field(None, description="Base token address")
    quote_token_address: Optional[str] = Field(None, description="Quote token address")
    reserve_in_usd: Optional[float] = Field(None, description="Total liquidity in USD")
    base_token_liquidity_usd: Optional[float] = Field(
        None, description="Base token liquidity in USD"
    )
    quote_token_liquidity_usd: Optional[float] = Field(
        None, description="Quote token liquidity in USD"
    )
    volume_24h_usd: Optional[float] = Field(None, description="24-hour volume in USD")
    price_usd: Optional[float] = Field(None, description="Current price in USD")
    price_change_24h: Optional[float] = Field(
        None, description="24-hour price change percentage"
    )


class TokenLiquidityData(BaseModel):
    """Liquidity data for a token across all pools."""

    token_address: str = Field(..., description="Token contract address")
    total_reserve_in_usd: Optional[float] = Field(
        None, description="Total liquidity across all pools in USD"
    )
    price_usd: Optional[float] = Field(None, description="Current price in USD")
    volume_24h_usd: Optional[float] = Field(None, description="24-hour volume in USD")
    price_change_24h: Optional[float] = Field(
        None, description="24-hour price change percentage"
    )
    top_pools: List[PoolLiquidityData] = Field(
        default_factory=list, description="Top pools for this token"
    )


class TrendingTokenData(BaseModel):
    """Data for a trending token."""

    token_address: str = Field(..., description="Token contract address")
    pool_address: Optional[str] = Field(None, description="Pool address if available")
    network: str = Field(..., description="Network ID")
    price_usd: Optional[float] = Field(None, description="Current price in USD")
    volume_24h_usd: Optional[float] = Field(None, description="24-hour volume in USD")
    reserve_in_usd: Optional[float] = Field(None, description="Liquidity in USD")
    price_change_24h: Optional[float] = Field(
        None, description="24-hour price change percentage"
    )


class MarketInsightsResponse(BaseModel):
    """Complete market insights response."""

    type: str = Field(default="market_insights", description="Response type")
    network: Optional[str] = Field(None, description="Network ID")
    token_address: Optional[str] = Field(None, description="Token address if specified")
    pool_address: Optional[str] = Field(None, description="Pool address if specified")

    # Liquidity data
    pool_liquidity: Optional[PoolLiquidityData] = Field(
        None, description="Pool liquidity data"
    )
    token_liquidity: Optional[TokenLiquidityData] = Field(
        None, description="Token liquidity data"
    )

    # Trending data
    trending_tokens: List[TrendingTokenData] = Field(
        default_factory=list, description="Trending tokens/pools"
    )

    # Price data
    price_usd: Optional[float] = Field(None, description="Current price in USD")
    volume_24h_usd: Optional[float] = Field(None, description="24-hour volume in USD")

    # Error handling
    error: Optional[str] = Field(None, description="Error message if any")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "market_insights",
                "network": "eth",
                "token_address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "price_usd": 3639.78,
                "volume_24h_usd": 12345678.90,
                "token_liquidity": {
                    "token_address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                    "total_reserve_in_usd": 1000000000.0,
                    "price_usd": 3639.78,
                    "volume_24h_usd": 12345678.90,
                    "price_change_24h": 2.5,
                    "top_pools": [],
                },
            }
        }

