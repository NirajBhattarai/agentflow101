"""
Price Impact Calculator Service

Calculates price impact for swaps using Uniswap V3 pool data.
"""

from typing import Dict
from ..core.models.routing import PoolData, PriceImpactData
from ..core.exceptions import InsufficientLiquidityError


def calculate_price_impact_simple(
    amount_in: float,
    pool_data: PoolData,
    token_in: str,
    token_out: str,
) -> PriceImpactData:
    """
    Calculate price impact using simplified constant product formula.

    For Uniswap V3, this is a simplified approximation. In production,
    you'd use the Quoter contract or SDK for accurate calculations.

    Args:
        amount_in: Input amount
        pool_data: Pool data with reserves
        token_in: Input token symbol
        token_out: Output token symbol

    Returns:
        PriceImpactData with calculated impact
    """
    # Determine which reserve is which
    if pool_data.token0.lower() == token_in.lower():
        reserve_in = pool_data.reserve_base
        reserve_out = pool_data.reserve_quote
    elif pool_data.token1.lower() == token_in.lower():
        reserve_in = pool_data.reserve_quote
        reserve_out = pool_data.reserve_base
    else:
        # Fallback: use reserves as-is
        reserve_in = pool_data.reserve_base
        reserve_out = pool_data.reserve_quote

    if reserve_in == 0 or reserve_out == 0:
        raise InsufficientLiquidityError(
            f"Insufficient liquidity in pool {pool_data.pool_address}"
        )

    # Calculate fee (in basis points)
    fee_bps = pool_data.fee_tier
    fee_percent = fee_bps / 10000.0

    # Constant product formula: (x + Δx) * (y - Δy) = x * y
    # After fee: (x + Δx * (1 - fee)) * (y - Δy) = x * y
    # Solving for Δy: Δy = (y * Δx * (1 - fee)) / (x + Δx * (1 - fee))

    amount_in_after_fee = amount_in * (1 - fee_percent)

    # Calculate output amount
    amount_out = (reserve_out * amount_in_after_fee) / (
        reserve_in + amount_in_after_fee
    )

    # Calculate effective price
    effective_price = amount_in / amount_out if amount_out > 0 else 0

    # Calculate spot price (before swap)
    spot_price = reserve_in / reserve_out if reserve_out > 0 else 0

    # Calculate price impact
    if spot_price > 0:
        price_impact_percent = abs((effective_price - spot_price) / spot_price) * 100
    else:
        price_impact_percent = 0

    # Fee cost
    fee_cost = amount_in * fee_percent

    return PriceImpactData(
        amount_in=amount_in,
        amount_out=amount_out,
        price_impact_percent=price_impact_percent,
        effective_price=effective_price,
        fee_cost=fee_cost,
    )


def calculate_price_impact_for_amounts(
    amounts: list[float],
    pool_data: PoolData,
    token_in: str,
    token_out: str,
) -> Dict[float, PriceImpactData]:
    """
    Calculate price impact for multiple amounts.

    Args:
        amounts: List of input amounts to test
        pool_data: Pool data
        token_in: Input token symbol
        token_out: Output token symbol

    Returns:
        Dictionary mapping amount -> PriceImpactData
    """
    results = {}
    for amount in amounts:
        try:
            impact = calculate_price_impact_simple(
                amount, pool_data, token_in, token_out
            )
            results[amount] = impact
        except InsufficientLiquidityError:
            # Skip amounts that exceed liquidity
            continue
    return results


def estimate_max_swap_amount(
    pool_data: PoolData,
    token_in: str,
    max_price_impact_percent: float = 3.0,
) -> float:
    """
    Estimate maximum swap amount for a given price impact threshold.

    Uses binary search to find the maximum amount that keeps price impact
    below the threshold.

    Args:
        pool_data: Pool data
        token_in: Input token symbol
        max_price_impact_percent: Maximum acceptable price impact

    Returns:
        Maximum swap amount
    """
    # Determine reserve
    if pool_data.token0.lower() == token_in.lower():
        reserve_in = pool_data.reserve_base
    elif pool_data.token1.lower() == token_in.lower():
        reserve_in = pool_data.reserve_quote
    else:
        reserve_in = pool_data.reserve_base

    # Binary search for max amount
    low = 0.0
    high = reserve_in * 0.5  # Don't swap more than 50% of reserve

    for _ in range(20):  # 20 iterations should be enough
        mid = (low + high) / 2
        try:
            impact = calculate_price_impact_simple(
                mid,
                pool_data,
                token_in,
                pool_data.token1
                if pool_data.token0.lower() == token_in.lower()
                else pool_data.token0,
            )
            if impact.price_impact_percent <= max_price_impact_percent:
                low = mid
            else:
                high = mid
        except InsufficientLiquidityError:
            high = mid

    return low
