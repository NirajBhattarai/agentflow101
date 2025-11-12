"""
Pool Calculator Agent Definition

An agent that processes liquidity and slot0 data from multiple chains,
analyzes price impacts, and uses LLM to recommend optimal swap routing
across chains.
"""

from .core.constants import (
    DEFAULT_USER_ID,
)
from .tools.calculations import (
    prepare_pools_by_chain,
    analyze_price_impact_for_allocation,
)


class PoolCalculatorAgent:
    """Agent that processes pool data and calculates optimal allocations directly (no LLM)."""

    def __init__(self):
        # No LLM agent needed - we do calculations directly
        self._user_id = DEFAULT_USER_ID

    def _parse_query_and_extract_data(self, query: str) -> dict:
        """Parse query to extract liquidity data, amount, and tokens."""
        import json
        import re

        result = {
            "liquidity_data": None,
            "total_amount": None,
            "token_in": None,
            "token_out": None,
        }

        # Extract amount and tokens from query
        amount_match = re.search(
            r"swapping\s+([\d,]+\.?\d*)\s+(\w+)\s+to\s+(\w+)", query, re.IGNORECASE
        )
        if amount_match:
            amount_str = amount_match.group(1).replace(",", "")
            result["total_amount"] = float(amount_str)
            result["token_in"] = amount_match.group(2).upper()
            result["token_out"] = amount_match.group(3).upper()

        # Extract liquidity data JSON
        json_start = query.find("{")
        if json_start >= 0:
            brace_count = 0
            json_end = json_start
            for i in range(json_start, len(query)):
                if query[i] == "{":
                    brace_count += 1
                elif query[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break

            if json_end > json_start:
                json_str = query[json_start:json_end]
                try:
                    result["liquidity_data"] = json.loads(json_str)
                except json.JSONDecodeError:
                    pass

        return result

    def _calculate_optimal_allocations(
        self,
        liquidity_data: dict,
        total_amount: float,
        token_in: str,
        token_out: str,
    ) -> dict:
        """Calculate optimal allocations using mathematical optimization."""

        # Prepare pools by chain
        pools_by_chain = prepare_pools_by_chain(liquidity_data)

        # Filter out chains with no pools
        available_chains = {k: v for k, v in pools_by_chain.items() if v}

        if not available_chains:
            return {
                "recommended_allocations": {},
                "total_output": 0.0,
                "average_price_impact": 0.0,
                "reasoning": "No pools available on any chain",
                "error": "No pools found",
            }

        # Gas costs per chain (in USD)
        GAS_COSTS = {
            "ethereum": 50.0,
            "polygon": 0.05,
            "hedera": 0.001,
        }

        # Test multiple allocation scenarios
        scenarios = []

        # Scenario 1: Proportional to TVL
        tvl_by_chain = {}
        total_tvl = 0.0
        for chain, pools in available_chains.items():
            if pools:
                tvl = sum(p.get("tvl_usd", 0.0) for p in pools)
                tvl_by_chain[chain] = tvl
                total_tvl += tvl

        if total_tvl > 0:
            allocations_tvl = {
                chain: (tvl / total_tvl) * total_amount
                for chain, tvl in tvl_by_chain.items()
            }
            result_tvl = analyze_price_impact_for_allocation(
                total_amount, allocations_tvl, pools_by_chain, token_in, token_out
            )
            scenarios.append(
                {
                    "name": "TVL Proportional",
                    "allocations": allocations_tvl,
                    "total_output": result_tvl["total_output"],
                    "avg_price_impact": result_tvl["average_price_impact"],
                    "result": result_tvl,
                }
            )

        # Scenario 2: Equal split
        num_chains = len(available_chains)
        if num_chains > 0:
            allocations_equal = {
                chain: total_amount / num_chains for chain in available_chains.keys()
            }
            result_equal = analyze_price_impact_for_allocation(
                total_amount, allocations_equal, pools_by_chain, token_in, token_out
            )
            scenarios.append(
                {
                    "name": "Equal Split",
                    "allocations": allocations_equal,
                    "total_output": result_equal["total_output"],
                    "avg_price_impact": result_equal["average_price_impact"],
                    "result": result_equal,
                }
            )

        # Scenario 3: Favor chains with deeper liquidity (weighted by reserve depth)
        if available_chains:
            reserve_weights = {}
            total_weight = 0.0
            for chain, pools in available_chains.items():
                if pools:
                    # Use the best pool (highest TVL)
                    best_pool = max(pools, key=lambda p: p.get("tvl_usd", 0.0))
                    reserve_in = best_pool.get("reserve_base", 0.0)
                    reserve_out = best_pool.get("reserve_quote", 0.0)
                    # Weight by geometric mean of reserves (liquidity depth)
                    weight = (reserve_in * reserve_out) ** 0.5
                    reserve_weights[chain] = weight
                    total_weight += weight

            if total_weight > 0:
                allocations_reserve = {
                    chain: (weight / total_weight) * total_amount
                    for chain, weight in reserve_weights.items()
                }
                result_reserve = analyze_price_impact_for_allocation(
                    total_amount,
                    allocations_reserve,
                    pools_by_chain,
                    token_in,
                    token_out,
                )
                scenarios.append(
                    {
                        "name": "Reserve Weighted",
                        "allocations": allocations_reserve,
                        "total_output": result_reserve["total_output"],
                        "avg_price_impact": result_reserve["average_price_impact"],
                        "result": result_reserve,
                    }
                )

        # Scenario 4: Favor Ethereum (deepest liquidity) but distribute to minimize impact
        if "ethereum" in available_chains and len(available_chains) > 1:
            # Allocate more to Ethereum, distribute rest
            eth_allocation = total_amount * 0.6
            remaining = total_amount - eth_allocation
            other_chains = [c for c in available_chains.keys() if c != "ethereum"]
            allocations_eth_favored = {"ethereum": eth_allocation}
            if other_chains:
                per_chain = remaining / len(other_chains)
                for chain in other_chains:
                    allocations_eth_favored[chain] = per_chain

            result_eth = analyze_price_impact_for_allocation(
                total_amount,
                allocations_eth_favored,
                pools_by_chain,
                token_in,
                token_out,
            )
            scenarios.append(
                {
                    "name": "Ethereum Favored",
                    "allocations": allocations_eth_favored,
                    "total_output": result_eth["total_output"],
                    "avg_price_impact": result_eth["average_price_impact"],
                    "result": result_eth,
                }
            )

        # Find best scenario (maximize output, minimize price impact)
        if not scenarios:
            return {
                "recommended_allocations": {},
                "total_output": 0.0,
                "average_price_impact": 0.0,
                "reasoning": "Could not calculate optimal allocations",
                "error": "No valid scenarios",
            }

        # Score each scenario: higher output is better, lower price impact is better
        best_scenario = max(
            scenarios, key=lambda s: s["total_output"] / max(s["avg_price_impact"], 0.1)
        )

        # Build reasoning
        reasoning_parts = [
            f"Analyzed {len(scenarios)} allocation scenarios.",
            f"Best: {best_scenario['name']} with {best_scenario['total_output']:.4f} {token_out} output",
            f"and {best_scenario['avg_price_impact']:.2f}% average price impact.",
        ]

        if len(available_chains) > 1:
            chain_details = []
            for chain, amount in best_scenario["allocations"].items():
                pct = (amount / total_amount) * 100
                chain_details.append(f"{chain}: {pct:.1f}% ({amount:,.0f} {token_in})")
            reasoning_parts.append(f"Allocation: {', '.join(chain_details)}.")

        return {
            "recommended_allocations": best_scenario["allocations"],
            "total_output": best_scenario["total_output"],
            "average_price_impact": best_scenario["avg_price_impact"],
            "reasoning": " ".join(reasoning_parts),
        }

    async def invoke(self, query: str, session_id: str) -> str:
        """
        Invoke the pool calculator agent with a query.
        Does calculations directly without LLM tool calls.

        Args:
            query: User query with pool data or calculation request
            session_id: Session ID

        Returns:
            JSON string with recommended allocations and analysis
        """
        print(f"🧮 Pool Calculator Agent received query: {query[:200]}...")

        try:
            import json

            # Parse query to extract data
            parsed = self._parse_query_and_extract_data(query)

            if not parsed["liquidity_data"]:
                return json.dumps(
                    {
                        "recommended_allocations": {},
                        "total_output": 0.0,
                        "average_price_impact": 0.0,
                        "reasoning": "Could not extract liquidity data from query",
                        "error": "No liquidity data found",
                    }
                )

            if (
                not parsed["total_amount"]
                or not parsed["token_in"]
                or not parsed["token_out"]
            ):
                return json.dumps(
                    {
                        "recommended_allocations": {},
                        "total_output": 0.0,
                        "average_price_impact": 0.0,
                        "reasoning": "Could not extract swap amount or tokens from query",
                        "error": "Missing swap parameters",
                    }
                )

            # Calculate optimal allocations directly
            result = self._calculate_optimal_allocations(
                parsed["liquidity_data"],
                parsed["total_amount"],
                parsed["token_in"],
                parsed["token_out"],
            )

            print(
                f"✅ Calculated optimal allocations: {result.get('recommended_allocations', {})}"
            )
            return json.dumps(result, indent=2)

        except Exception as e:
            error_msg = f"Error in Pool Calculator Agent: {e}"
            print(f"❌ {error_msg}")
            import traceback

            traceback.print_exc()
            import json

            return json.dumps(
                {
                    "recommended_allocations": {},
                    "total_output": 0.0,
                    "average_price_impact": 0.0,
                    "reasoning": f"Error: {error_msg}",
                    "error": error_msg,
                }
            )
