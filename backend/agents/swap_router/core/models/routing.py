"""
Routing domain models for Swap Router Agent.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class PoolData(BaseModel):
    """Represents pool data for routing calculations."""

    chain: str = Field(description="Chain name")
    pool_address: str = Field(description="Pool contract address")
    token0: str = Field(description="Token0 symbol")
    token1: str = Field(description="Token1 symbol")
    fee_tier: int = Field(description="Fee tier in basis points")
    liquidity: Optional[str] = Field(default=None, description="Pool liquidity")
    slot0: Optional[dict] = Field(default=None, description="Uniswap V3 slot0 data")
    sqrt_price_x96: Optional[str] = Field(
        default=None, description="sqrtPriceX96 from slot0"
    )
    tick: Optional[int] = Field(default=None, description="Current tick")
    reserve_base: float = Field(default=0.0, description="Base token reserve")
    reserve_quote: float = Field(default=0.0, description="Quote token reserve")
    tvl_usd: float = Field(default=0.0, description="Total Value Locked in USD")


class PriceImpactData(BaseModel):
    """Price impact data for a swap amount."""

    amount_in: float = Field(description="Input amount")
    amount_out: float = Field(description="Expected output amount")
    price_impact_percent: float = Field(description="Price impact percentage")
    effective_price: float = Field(description="Effective price (in/out)")
    fee_cost: float = Field(description="Fee cost in input token")


class RouteRecommendation(BaseModel):
    """A single route recommendation for a chain."""

    chain: str = Field(description="Chain name")
    chain_id: Optional[int] = Field(default=None, description="Chain ID")
    amount_in: float = Field(description="Input amount")
    token_in: str = Field(description="Input token symbol")
    amount_out: float = Field(description="Expected output amount")
    token_out: str = Field(description="Output token symbol")
    price_impact_percent: float = Field(description="Price impact percentage")
    pool: PoolData = Field(description="Pool data")
    gas_cost_usd: float = Field(description="Estimated gas cost in USD")
    execution_time_seconds: int = Field(
        description="Estimated execution time in seconds"
    )
    confidence: float = Field(default=0.9, description="Confidence score (0-1)")
    route_description: str = Field(description="Human-readable route description")


class SwapRouterRecommendation(BaseModel):
    """Complete swap routing recommendation."""

    type: str = Field(default="swap_router", description="Response type")
    total_input: float = Field(description="Total input amount")
    token_in: str = Field(description="Input token symbol")
    total_output: float = Field(description="Total expected output amount")
    token_out: str = Field(description="Output token symbol")
    total_price_impact_percent: float = Field(
        description="Weighted average price impact"
    )
    total_gas_cost_usd: float = Field(description="Total gas cost in USD")
    net_output: float = Field(description="Net output after gas costs")
    efficiency_percent: float = Field(description="Efficiency percentage (0-100)")
    routes: List[RouteRecommendation] = Field(
        description="Route recommendations per chain"
    )
    recommendation_text: str = Field(description="Human-readable recommendation")
    execution_plan: Optional[List[dict]] = Field(
        default=None, description="Step-by-step execution plan"
    )
    error: Optional[str] = Field(default=None, description="Error message if any")
