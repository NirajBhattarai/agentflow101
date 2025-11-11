"""
Pydantic models for Multi-Chain Liquidity Agent.
"""

from typing import Optional
from pydantic import BaseModel, Field
from ..constants import RESPONSE_TYPE


class LiquidityPair(BaseModel):
    """Represents a liquidity pair/pool."""

    base: str = Field(description="Base token symbol")
    quote: str = Field(description="Quote token symbol")
    pool_address: str = Field(description="Pool contract address")
    dex: str = Field(description="DEX name (e.g., SaucerSwap, HeliSwap, QuickSwap)")
    tvl_usd: float = Field(description="Total Value Locked in USD")
    reserve_base: float = Field(description="Base token reserve")
    reserve_quote: float = Field(description="Quote token reserve")
    fee_bps: int = Field(description="Fee in basis points")
    chain: str = Field(description="Chain name: polygon, hedera, or ethereum")
    liquidity: Optional[str] = Field(default=None, description="Pool liquidity value")
    slot0: Optional[dict] = Field(
        default=None, description="Uniswap V3 slot0 data (sqrtPriceX96, tick, etc.)"
    )


class StructuredMultiChainLiquidity(BaseModel):
    """Structured response for multi-chain liquidity queries."""

    type: str = Field(default=RESPONSE_TYPE, description="Response type")
    token_pair: Optional[str] = Field(
        default=None, description="Token pair queried (e.g., ETH/USDT) if provided"
    )
    chain: Optional[str] = Field(
        default=None, description="Chain queried (hedera, polygon, ethereum, or all)"
    )
    chains: dict = Field(description="Liquidity data by chain")
    hedera_pairs: list[LiquidityPair] = Field(
        default=[], description="Hedera liquidity pairs"
    )
    polygon_pairs: list[LiquidityPair] = Field(
        default=[], description="Polygon liquidity pairs"
    )
    ethereum_pairs: list[LiquidityPair] = Field(
        default=[], description="Ethereum liquidity pairs"
    )
    all_pairs: list[LiquidityPair] = Field(
        default=[], description="All liquidity pairs combined"
    )
    error: Optional[str] = Field(default=None, description="Error message if any")
