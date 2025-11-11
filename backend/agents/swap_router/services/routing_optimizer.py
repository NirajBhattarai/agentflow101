"""
Routing Optimizer Service

Optimizes swap routing across multiple chains using iterative allocation algorithm.
"""

from typing import List, Dict, Optional
from ..core.models.routing import PoolData, RouteRecommendation, SwapRouterRecommendation
from ..core.constants import (
    DEFAULT_MAX_SLIPPAGE_PERCENT,
    DEFAULT_MAX_GAS_SPEND_USD,
    DEFAULT_ALLOCATION_STEP,
    DEFAULT_MAX_ITERATIONS,
    GAS_COST_ESTIMATES,
    EXECUTION_TIME_ESTIMATES,
)
from .price_impact_calculator import calculate_price_impact_simple


def calculate_marginal_cost(
    current_amount: float,
    pool_data: PoolData,
    token_in: str,
    token_out: str,
    gas_cost_usd: float,
) -> float:
    """
    Calculate marginal cost (price impact + gas) for allocating next increment.
    
    Args:
        current_amount: Current allocated amount
        pool_data: Pool data
        token_in: Input token symbol
        token_out: Output token symbol
        gas_cost_usd: Gas cost in USD
        
    Returns:
        Marginal cost (weighted combination of price impact and gas)
    """
    if current_amount == 0:
        # Initial allocation - include full gas cost
        try:
            impact = calculate_price_impact_simple(
                DEFAULT_ALLOCATION_STEP, pool_data, token_in, token_out
            )
            return impact.price_impact_percent + (gas_cost_usd / DEFAULT_ALLOCATION_STEP * 100)
        except Exception:
            return float('inf')
    
    # Calculate marginal impact for next increment
    try:
        impact_before = calculate_price_impact_simple(
            current_amount, pool_data, token_in, token_out
        )
        impact_after = calculate_price_impact_simple(
            current_amount + DEFAULT_ALLOCATION_STEP, pool_data, token_in, token_out
        )
        
        marginal_impact = impact_after.price_impact_percent - impact_before.price_impact_percent
        marginal_gas = (gas_cost_usd / (current_amount + DEFAULT_ALLOCATION_STEP)) * 100
        
        return marginal_impact + marginal_gas
    except Exception:
        return float('inf')


def optimize_routing(
    total_amount: float,
    token_in: str,
    token_out: str,
    pools_by_chain: Dict[str, List[PoolData]],
    max_slippage_percent: float = DEFAULT_MAX_SLIPPAGE_PERCENT,
    max_gas_usd: float = DEFAULT_MAX_GAS_SPEND_USD,
) -> SwapRouterRecommendation:
    """
    Optimize swap routing across multiple chains.
    
    Uses iterative greedy algorithm to allocate amounts across chains
    to minimize total cost (price impact + gas).
    
    Args:
        total_amount: Total amount to swap
        token_in: Input token symbol
        token_out: Output token symbol
        pools_by_chain: Dictionary mapping chain -> list of pools
        max_slippage_percent: Maximum acceptable slippage
        max_gas_usd: Maximum gas spend in USD
        
    Returns:
        SwapRouterRecommendation with optimal routing
    """
    # Select best pool per chain (highest liquidity)
    best_pools = {}
    for chain, pools in pools_by_chain.items():
        if not pools:
            continue
        # Select pool with highest TVL
        best_pool = max(pools, key=lambda p: p.tvl_usd)
        best_pools[chain] = best_pool
    
    if not best_pools:
        raise ValueError("No pools available for routing")
    
    # Initialize allocation
    allocations = {chain: 0.0 for chain in best_pools.keys()}
    remaining = total_amount
    
    # Iterative allocation
    iterations = 0
    while remaining > DEFAULT_ALLOCATION_STEP and iterations < DEFAULT_MAX_ITERATIONS:
        # Calculate marginal cost for each chain
        marginal_costs = {}
        for chain, pool in best_pools.items():
            gas_cost = GAS_COST_ESTIMATES.get(chain, {}).get("swap", 50.0)
            marginal_costs[chain] = calculate_marginal_cost(
                allocations[chain], pool, token_in, token_out, gas_cost
            )
        
        # Find chain with minimum marginal cost
        if not marginal_costs:
            break
        
        best_chain = min(marginal_costs.keys(), key=lambda c: marginal_costs[c])
        
        # Check if allocation is valid
        allocation_step = min(DEFAULT_ALLOCATION_STEP, remaining)
        
        # Verify price impact is acceptable
        pool = best_pools[best_chain]
        try:
            impact = calculate_price_impact_simple(
                allocations[best_chain] + allocation_step,
                pool,
                token_in,
                token_out,
            )
            if impact.price_impact_percent > max_slippage_percent:
                # This chain is too expensive, remove it
                del best_pools[best_chain]
                if best_chain in allocations:
                    remaining += allocations[best_chain]
                    allocations[best_chain] = 0
                continue
        except Exception:
            # Pool can't handle this amount, remove it
            del best_pools[best_chain]
            if best_chain in allocations:
                remaining += allocations[best_chain]
                allocations[best_chain] = 0
            continue
        
        # Allocate increment
        allocations[best_chain] += allocation_step
        remaining -= allocation_step
        iterations += 1
    
    # If there's remaining amount, distribute proportionally
    if remaining > 0 and best_pools:
        # Distribute remaining based on current allocations
        total_allocated = sum(allocations.values())
        if total_allocated > 0:
            for chain in allocations:
                if chain in best_pools:
                    proportion = allocations[chain] / total_allocated
                    allocations[chain] += remaining * proportion
        else:
            # Equal distribution
            per_chain = remaining / len(best_pools)
            for chain in best_pools:
                allocations[chain] += per_chain
        remaining = 0
    
    # Build route recommendations
    routes = []
    total_output = 0.0
    total_price_impact_weighted = 0.0
    total_gas_cost = 0.0
    
    for chain, amount in allocations.items():
        if amount <= 0 or chain not in best_pools:
            continue
        
        pool = best_pools[chain]
        gas_cost = GAS_COST_ESTIMATES.get(chain, {}).get("swap", 50.0)
        exec_time = EXECUTION_TIME_ESTIMATES.get(chain, 60)
        
        # Calculate output and impact
        try:
            impact = calculate_price_impact_simple(amount, pool, token_in, token_out)
            
            route = RouteRecommendation(
                chain=chain,
                chain_id=_get_chain_id(chain),
                amount_in=amount,
                token_in=token_in,
                amount_out=impact.amount_out,
                token_out=token_out,
                price_impact_percent=impact.price_impact_percent,
                pool=pool,
                gas_cost_usd=gas_cost,
                execution_time_seconds=exec_time,
                confidence=0.9 if impact.price_impact_percent < 2.0 else 0.7,
                route_description=f"Swap {amount:,.0f} {token_in} → {impact.amount_out:.4f} {token_out} on {chain.capitalize()}",
            )
            
            routes.append(route)
            total_output += impact.amount_out
            total_price_impact_weighted += impact.price_impact_percent * amount
            total_gas_cost += gas_cost
        except Exception as e:
            print(f"Error calculating route for {chain}: {e}")
            continue
    
    if not routes:
        raise ValueError("No valid routes found")
    
    # Calculate totals
    total_input_used = sum(r.amount_in for r in routes)
    avg_price_impact = total_price_impact_weighted / total_input_used if total_input_used > 0 else 0
    net_output = total_output  # Gas already accounted for separately
    efficiency = (net_output / (total_input_used * _get_spot_price(token_in, token_out))) * 100 if total_input_used > 0 else 0
    
    # Build recommendation text
    recommendation_text = _build_recommendation_text(routes, total_input_used, total_output, avg_price_impact, total_gas_cost)
    
    return SwapRouterRecommendation(
        type="swap_router",
        total_input=total_input_used,
        token_in=token_in,
        total_output=total_output,
        token_out=token_out,
        total_price_impact_percent=avg_price_impact,
        total_gas_cost_usd=total_gas_cost,
        net_output=net_output,
        efficiency_percent=efficiency,
        routes=routes,
        recommendation_text=recommendation_text,
    )


def _get_chain_id(chain: str) -> Optional[int]:
    """Get chain ID for a chain name."""
    chain_ids = {
        "ethereum": 1,
        "polygon": 137,
        "hedera": 295,  # Hedera mainnet
    }
    return chain_ids.get(chain.lower())


def _get_spot_price(token_in: str, token_out: str) -> float:
    """Get approximate spot price (simplified - would use oracle in production)."""
    # This is a placeholder - in production, fetch from price oracle
    return 1.0


def _build_recommendation_text(
    routes: List[RouteRecommendation],
    total_input: float,
    total_output: float,
    avg_price_impact: float,
    total_gas: float,
) -> str:
    """Build human-readable recommendation text."""
    text = f"Optimal routing found for {total_input:,.0f} {routes[0].token_in if routes else 'tokens'}:\n\n"
    
    for i, route in enumerate(routes, 1):
        text += f"Route {i}: {route.chain.capitalize()} ({route.amount_in/total_input*100:.0f}%)\n"
        text += f"  - Amount: {route.amount_in:,.0f} {route.token_in} → {route.amount_out:.4f} {route.token_out}\n"
        text += f"  - Price Impact: {route.price_impact_percent:.2f}%\n"
        text += f"  - Gas Cost: ${route.gas_cost_usd:.2f}\n"
        text += f"  - Execution Time: {route.execution_time_seconds}s\n\n"
    
    text += f"Total Output: {total_output:.4f} {routes[0].token_out if routes else 'tokens'}\n"
    text += f"Average Price Impact: {avg_price_impact:.2f}%\n"
    text += f"Total Gas Cost: ${total_gas:.2f}"
    
    return text

