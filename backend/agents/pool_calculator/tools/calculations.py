"""
Calculation tools for pool data analysis.

These tools perform various calculations on liquidity and slot0 data.
"""

from typing import Dict, Optional, List
from decimal import Decimal, getcontext
from ..core.exceptions import InvalidPoolDataError, CalculationError, InsufficientDataError
import json

# Set high precision for calculations
getcontext().prec = 50

# Constants
Q96 = 2**96  # 2^96 used in Uniswap V3


def calculate_price_from_sqrt_price_x96(
    sqrt_price_x96: str,
    token0_decimals: int,
    token1_decimals: int,
) -> Dict[str, float]:
    """
    Calculate human-readable price from sqrtPriceX96.
    
    Args:
        sqrt_price_x96: sqrtPriceX96 value as string
        token0_decimals: Decimals for token0
        token1_decimals: Decimals for token1
    
    Returns:
        Dictionary with price information
    """
    try:
        sqrt_price_x96_decimal = Decimal(str(sqrt_price_x96))
        sqrt_price = sqrt_price_x96_decimal / Decimal(Q96)
        price_wei = sqrt_price ** 2
        
        # Convert to human-readable: price_human = price_wei * 10^(decimals0 - decimals1)
        # price_wei = token1_wei / token0_wei
        # price_human = (token1_wei / 10^decimals1) / (token0_wei / 10^decimals0)
        #             = price_wei * 10^(decimals0 - decimals1)
        decimal_adjustment = Decimal(10) ** (token0_decimals - token1_decimals)
        price_token1_per_token0 = float(price_wei * decimal_adjustment)
        
        # If price is unreasonably small, try inverted adjustment
        if price_token1_per_token0 < 1e-10 and float(price_wei) > 1e-6:
            # Likely inverted: try the opposite
            decimal_adjustment_inv = Decimal(10) ** (token1_decimals - token0_decimals)
            price_token1_per_token0 = float(price_wei * decimal_adjustment_inv)
        
        return {
            "price_token1_per_token0": price_token1_per_token0,
            "price_token0_per_token1": 1.0 / price_token1_per_token0 if price_token1_per_token0 > 0 else 0,
            "price_wei": float(price_wei),
        }
    except Exception as e:
        raise CalculationError(f"Failed to calculate price from sqrtPriceX96: {e}")


def calculate_swap_output(
    amount_in: float,
    reserve_in: float,
    reserve_out: float,
    fee_percent: float = 0.003,  # 0.3% default fee
) -> Dict[str, float]:
    """
    Calculate swap output using constant product formula.
    
    Args:
        amount_in: Input amount
        reserve_in: Input token reserve
        reserve_out: Output token reserve
        fee_percent: Fee percentage (default 0.3%)
    
    Returns:
        Dictionary with swap output information
    """
    if reserve_in <= 0 or reserve_out <= 0:
        raise InvalidPoolDataError("Reserves must be positive")
    
    if amount_in <= 0:
        raise InvalidPoolDataError("Input amount must be positive")
    
    # Constant product formula: (x + Δx * (1 - fee)) * (y - Δy) = x * y
    # Solving for Δy: Δy = (y * Δx * (1 - fee)) / (x + Δx * (1 - fee))
    amount_in_after_fee = amount_in * (1 - fee_percent)
    amount_out = (reserve_out * amount_in_after_fee) / (reserve_in + amount_in_after_fee)
    
    # Calculate effective price
    effective_price = amount_in / amount_out if amount_out > 0 else 0
    
    # Calculate spot price
    spot_price = reserve_in / reserve_out if reserve_out > 0 else 0
    
    # Calculate price impact
    price_impact_percent = abs((effective_price - spot_price) / spot_price) * 100 if spot_price > 0 else 0
    
    return {
        "amount_out": amount_out,
        "effective_price": effective_price,
        "spot_price": spot_price,
        "price_impact_percent": price_impact_percent,
        "fee_cost": amount_in * fee_percent,
    }


def analyze_pool_health(
    reserve_base: float,
    reserve_quote: float,
    tvl_usd: float,
    fee_bps: int,
) -> Dict[str, any]:
    """
    Analyze pool health metrics.
    
    Args:
        reserve_base: Base token reserve
        reserve_quote: Quote token reserve
        tvl_usd: Total Value Locked in USD
        fee_bps: Fee in basis points
    
    Returns:
        Dictionary with health metrics
    """
    # Calculate reserve ratio
    reserve_ratio = reserve_base / reserve_quote if reserve_quote > 0 else 0
    
    # Determine if pool is balanced (within 20% of 1:1)
    is_balanced = 0.8 <= reserve_ratio <= 1.2
    
    # Calculate liquidity depth (average of reserves)
    liquidity_depth = (reserve_base + reserve_quote) / 2
    
    # Fee percentage
    fee_percent = fee_bps / 10000.0
    
    return {
        "reserve_ratio": reserve_ratio,
        "is_balanced": is_balanced,
        "liquidity_depth": liquidity_depth,
        "tvl_usd": tvl_usd,
        "fee_percent": fee_percent,
        "health_score": "good" if is_balanced and tvl_usd > 100000 else "moderate",
    }


def process_pool_data(
    pool_data: Dict,
) -> Dict[str, any]:
    """
    Process pool data and perform all calculations.
    
    Args:
        pool_data: Dictionary with pool data including liquidity, slot0, reserves, etc.
    
    Returns:
        Dictionary with all calculated metrics and insights
    """
    results = {
        "pool_address": pool_data.get("pool_address", ""),
        "token0": pool_data.get("token0", ""),
        "token1": pool_data.get("token1", ""),
        "calculations": {},
        "insights": [],
    }
    
    # Get slot0 data
    slot0 = pool_data.get("slot0", {})
    sqrt_price_x96 = slot0.get("sqrtPriceX96") if slot0 else None
    
    # Get reserves
    reserve_base = pool_data.get("reserve_base", 0.0)
    reserve_quote = pool_data.get("reserve_quote", 0.0)
    
    # Get token decimals (defaults)
    token0_decimals = 18  # Default, should be fetched from token contract
    token1_decimals = 18
    
    # Calculate price from sqrtPriceX96 if available
    if sqrt_price_x96:
        try:
            price_info = calculate_price_from_sqrt_price_x96(
                sqrt_price_x96, token0_decimals, token1_decimals
            )
            results["calculations"]["price"] = price_info
            results["insights"].append(
                f"Current price: {price_info['price_token1_per_token0']:.6f} {pool_data.get('token1', 'token1')} per {pool_data.get('token0', 'token0')}"
            )
        except Exception as e:
            results["insights"].append(f"Could not calculate price from sqrtPriceX96: {e}")
    
    # Analyze pool health
    if reserve_base > 0 and reserve_quote > 0:
        health = analyze_pool_health(
            reserve_base,
            reserve_quote,
            pool_data.get("tvl_usd", 0.0),
            pool_data.get("fee_bps", 3000),
        )
        results["calculations"]["health"] = health
        results["insights"].append(
            f"Pool health: {health['health_score']}, Reserve ratio: {health['reserve_ratio']:.2f}"
        )
    
    return results


def prepare_pools_by_chain(
    liquidity_data: Dict,
) -> Dict[str, List[Dict]]:
    """
    Prepare pools data organized by chain from multichain_liquidity response.
    
    Args:
        liquidity_data: Response from multichain_liquidity agent
    
    Returns:
        Dictionary mapping chain -> list of pool dictionaries
    """
    pools_by_chain = {
        "ethereum": [],
        "polygon": [],
        "hedera": [],
    }
    
    chains = liquidity_data.get("chains", {})
    
    for chain_name, chain_data in chains.items():
        pairs = chain_data.get("pairs", [])
        pools_by_chain[chain_name] = pairs
    
    return pools_by_chain


def analyze_price_impact_for_allocation(
    total_amount: float,
    allocations: Dict[str, float],
    pools_by_chain: Dict[str, List[Dict]],
    token_in: str,
    token_out: str,
) -> Dict[str, any]:
    """
    Analyze price impact for different allocation strategies across chains.
    
    Args:
        total_amount: Total amount to swap
        allocations: Dictionary mapping chain -> amount (e.g., {"ethereum": 500000, "polygon": 300000})
        pools_by_chain: Dictionary mapping chain -> list of pool data
        token_in: Input token symbol
        token_out: Output token symbol
    
    Returns:
        Dictionary with analysis results including:
        - total_output: Total ETH/token_out received
        - price_impacts: Price impact per chain
        - recommendations: LLM-friendly recommendations
    """
    results = {
        "total_input": total_amount,
        "token_in": token_in,
        "token_out": token_out,
        "allocations": allocations,
        "chain_results": {},
        "total_output": 0.0,
        "average_price_impact": 0.0,
        "recommendations": [],
    }
    
    total_output = 0.0
    total_price_impact_weighted = 0.0
    total_input_used = 0.0
    
    for chain, amount in allocations.items():
        if amount <= 0:
            continue
        
        pools = pools_by_chain.get(chain, [])
        if not pools:
            results["chain_results"][chain] = {
                "amount": amount,
                "output": 0.0,
                "price_impact": 0.0,
                "error": "No pools available",
            }
            continue
        
        # Use the first/best pool for calculation
        pool = pools[0]
        
        # Get reserves
        reserve_base = pool.get("reserve_base", 0.0)
        reserve_quote = pool.get("reserve_quote", 0.0)
        fee_bps = pool.get("fee_bps", 3000)
        fee_percent = fee_bps / 10000.0
        
        # Determine which reserve is which based on token symbols
        token0 = pool.get("token0", "").upper()
        token1 = pool.get("token1", "").upper()
        token_in_upper = token_in.upper()
        token_out_upper = token_out.upper()
        
        # Normalize ETH -> WETH
        if token_in_upper == "ETH":
            token_in_upper = "WETH"
        if token_out_upper == "ETH":
            token_out_upper = "WETH"
        if token0 == "ETH":
            token0 = "WETH"
        if token1 == "ETH":
            token1 = "WETH"
        
        # Determine swap direction
        if token0 == token_in_upper:
            reserve_in = reserve_base
            reserve_out = reserve_quote
        elif token1 == token_in_upper:
            reserve_in = reserve_quote
            reserve_out = reserve_base
        else:
            # Fallback
            reserve_in = reserve_base
            reserve_out = reserve_quote
        
        # Calculate swap output
        try:
            swap_result = calculate_swap_output(
                amount, reserve_in, reserve_out, fee_percent
            )
            
            chain_output = swap_result["amount_out"]
            chain_price_impact = swap_result["price_impact_percent"]
            
            total_output += chain_output
            total_price_impact_weighted += chain_price_impact * amount
            total_input_used += amount
            
            results["chain_results"][chain] = {
                "amount": amount,
                "output": chain_output,
                "price_impact": chain_price_impact,
                "effective_price": swap_result["effective_price"],
                "pool_address": pool.get("pool_address", ""),
            }
        except Exception as e:
            results["chain_results"][chain] = {
                "amount": amount,
                "output": 0.0,
                "price_impact": 0.0,
                "error": str(e),
            }
    
    results["total_output"] = total_output
    results["average_price_impact"] = (
        total_price_impact_weighted / total_input_used if total_input_used > 0 else 0
    )
    
    # Generate recommendations
    if results["chain_results"]:
        best_chain = max(
            results["chain_results"].items(),
            key=lambda x: x[1].get("output", 0) / max(x[1].get("amount", 1), 1),
        )[0]
        results["recommendations"].append(
            f"Best efficiency: {best_chain} with {results['chain_results'][best_chain]['output']:.4f} {token_out} output"
        )
    
    return results

