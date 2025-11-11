"""
Price Impact Calculator Service

Calculates price impact for swaps using Uniswap V3 pool data with slot0 (sqrtPriceX96).
"""

from typing import Dict
from decimal import Decimal, getcontext
from ..core.models.routing import PoolData, PriceImpactData
from ..core.exceptions import InsufficientLiquidityError

# Set high precision for calculations
getcontext().prec = 50

# Constants
Q96 = 2**96  # 2^96 used in Uniswap V3


def calculate_price_impact_simple(
    amount_in: float,
    pool_data: PoolData,
    token_in: str,
    token_out: str,
) -> PriceImpactData:
    """
    Calculate price impact using Uniswap V3 sqrtPriceX96 formula.

    Uses slot0.sqrtPriceX96 for accurate Uniswap V3 calculations.
    Falls back to constant product formula if sqrtPriceX96 is not available.

    Args:
        amount_in: Input amount
        pool_data: Pool data with reserves and slot0
        token_in: Input token symbol
        token_out: Output token symbol

    Returns:
        PriceImpactData with calculated impact
    """
    # Normalize token symbols for matching
    token_in_norm = token_in.upper()
    token_out_norm = token_out.upper()
    token0_norm = pool_data.token0.upper()
    token1_norm = pool_data.token1.upper()
    
    # Map ETH to WETH for matching
    if token_in_norm == "ETH":
        token_in_norm = "WETH"
    if token_out_norm == "ETH":
        token_out_norm = "WETH"
    if token0_norm == "ETH":
        token0_norm = "WETH"
    if token1_norm == "ETH":
        token1_norm = "WETH"
    
    # Determine swap direction (token0 -> token1 or token1 -> token0)
    is_token0_in = token0_norm == token_in_norm
    is_token1_in = token1_norm == token_in_norm
    
    if not is_token0_in and not is_token1_in:
        print(f"⚠️  Token mismatch: pool has {pool_data.token0}/{pool_data.token1}, swap is {token_in}/{token_out}")
        # Fallback: assume token0 is input
        is_token0_in = True

    # Calculate fee (in basis points)
    fee_bps = pool_data.fee_tier
    fee_percent = fee_bps / 10000.0
    amount_in_after_fee = amount_in * (1 - fee_percent)

    # Use sqrtPriceX96 if available (Uniswap V3)
    if pool_data.sqrt_price_x96:
        try:
            return _calculate_with_sqrt_price_x96(
                amount_in,
                amount_in_after_fee,
                pool_data,
                token_in_norm,
                token_out_norm,
                is_token0_in,
                fee_percent,
            )
        except Exception as e:
            print(f"⚠️  Error calculating with sqrtPriceX96: {e}, falling back to constant product")
            # Fall back to constant product formula

    # Fallback to constant product formula
    return _calculate_with_constant_product(
        amount_in,
        amount_in_after_fee,
        pool_data,
        token_in_norm,
        token_out_norm,
        is_token0_in,
        fee_percent,
    )


def _calculate_with_sqrt_price_x96(
    amount_in: float,
    amount_in_after_fee: float,
    pool_data: PoolData,
    token_in_norm: str,
    token_out_norm: str,
    is_token0_in: bool,
    fee_percent: float,
) -> PriceImpactData:
    """
    Calculate swap output using Uniswap V3 sqrtPriceX96 formula.
    
    Formula:
    - sqrtPriceX96 = sqrt(price) * 2^96
    - price = (sqrtPriceX96 / 2^96)^2
    - For token0 -> token1: price = token1_amount / token0_amount
    - For token1 -> token0: price = token0_amount / token1_amount = 1/(token1/token0)
    
    Uses constant product formula with reserves, but validates spot price from sqrtPriceX96.
    """
    sqrt_price_x96_str = pool_data.sqrt_price_x96
    if isinstance(sqrt_price_x96_str, str):
        sqrt_price_x96 = Decimal(sqrt_price_x96_str)
    else:
        sqrt_price_x96 = Decimal(str(sqrt_price_x96_str))
    
    # Current price from sqrtPriceX96: price = (sqrtPriceX96 / Q96)^2
    # This represents token1/token0 ratio (in token units, accounting for decimals)
    sqrt_price = sqrt_price_x96 / Decimal(Q96)
    price_token1_per_token0 = float(sqrt_price ** 2)
    
    # Get reserves (these might be in wei/smallest units, so we'll use them carefully)
    if is_token0_in:
        reserve_in = Decimal(str(pool_data.reserve_base))
        reserve_out = Decimal(str(pool_data.reserve_quote))
        # Spot price = token1/token0 = price from sqrtPriceX96
        spot_price = price_token1_per_token0
    else:
        reserve_in = Decimal(str(pool_data.reserve_quote))
        reserve_out = Decimal(str(pool_data.reserve_base))
        # Spot price = token0/token1 = 1/(token1/token0) = 1/price_from_sqrtPriceX96
        spot_price = 1.0 / price_token1_per_token0 if price_token1_per_token0 > 0 else 0
    
    if reserve_in == 0 or reserve_out == 0:
        raise InsufficientLiquidityError(
            f"Insufficient liquidity in pool {pool_data.pool_address}"
        )
    
    # Convert amount_in to Decimal for precision
    amount_in_decimal = Decimal(str(amount_in_after_fee))
    
    # Method 1: Use spot price from sqrtPriceX96 for initial estimate
    # This gives us the current exchange rate
    estimated_amount_out_from_price = float(amount_in_decimal) * spot_price
    
    # Method 2: Use constant product formula with reserves
    # This accounts for slippage
    # (reserve_in + amount_in) * (reserve_out - amount_out) = reserve_in * reserve_out
    # Solving for amount_out:
    # amount_out = (reserve_out * amount_in) / (reserve_in + amount_in)
    
    # Check if reserves seem reasonable (not in wei)
    # If reserves are way larger than amount_in, they might be in wei
    reserve_ratio = float(reserve_in / amount_in_decimal) if amount_in_decimal > 0 else 0
    
    if reserve_ratio > 1e12:  # Reserves are way too large, likely in wei
        # Use price-based calculation directly
        amount_out = estimated_amount_out_from_price
        print(f"⚠️  Reserves appear to be in wei (ratio={reserve_ratio:.2e}), using price-based calculation")
    else:
        # Use constant product formula (normal case)
        amount_out_decimal = (reserve_out * amount_in_decimal) / (reserve_in + amount_in_decimal)
        amount_out = float(amount_out_decimal)
        
        # Validate against price-based estimate (should be close for small swaps)
        if estimated_amount_out_from_price > 0:
            diff_ratio = abs(amount_out - estimated_amount_out_from_price) / estimated_amount_out_from_price
            if diff_ratio > 0.5:  # More than 50% difference, something's wrong
                print(f"⚠️  Large difference between methods: constant_product={amount_out:.6f}, price_based={estimated_amount_out_from_price:.6f}")
                # Use price-based as fallback
                amount_out = estimated_amount_out_from_price
    
    # Calculate effective price (amount_in / amount_out)
    effective_price = amount_in / amount_out if amount_out > 0 else 0
    
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


def _calculate_with_constant_product(
    amount_in: float,
    amount_in_after_fee: float,
    pool_data: PoolData,
    token_in_norm: str,
    token_out_norm: str,
    is_token0_in: bool,
    fee_percent: float,
) -> PriceImpactData:
    """
    Fallback: Calculate using constant product formula with reserves.
    """
    # Determine which reserve is which
    if is_token0_in:
        reserve_in = pool_data.reserve_base
        reserve_out = pool_data.reserve_quote
    else:
        reserve_in = pool_data.reserve_quote
        reserve_out = pool_data.reserve_base

    if reserve_in == 0 or reserve_out == 0:
        raise InsufficientLiquidityError(
            f"Insufficient liquidity in pool {pool_data.pool_address}"
        )

    # Constant product formula: (x + Δx) * (y - Δy) = x * y
    # After fee: (x + Δx * (1 - fee)) * (y - Δy) = x * y
    # Solving for Δy: Δy = (y * Δx * (1 - fee)) / (x + Δx * (1 - fee))

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
