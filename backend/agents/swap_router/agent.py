"""
Swap Router Agent Definition

An intelligent agent that optimizes large token swaps across multiple chains.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService

from .core.constants import (
    AGENT_NAME,
    AGENT_DESCRIPTION,
    get_model_name,
    check_api_keys,
    DEFAULT_USER_ID,
)
from .core.agent_instruction import AGENT_INSTRUCTION
from .services.query_parser import parse_swap_router_query
from .services.liquidity_fetcher import (
    fetch_liquidity_from_multichain_agent,
    convert_liquidity_to_pool_data,
)
from .services.pool_calculator_client import get_optimal_allocations_from_pool_calculator
from .services.routing_optimizer import optimize_routing
from .services.response_builder import build_routing_response, build_error_response
from .core.exceptions import SwapRouterError


class SwapRouterAgent:
    """Agent that optimizes swap routing across multiple chains."""

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = DEFAULT_USER_ID
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def _build_agent(self) -> LlmAgent:
        """Build and configure the LLM agent."""
        model_name = get_model_name()
        check_api_keys()

        return LlmAgent(
            model=model_name,
            name=AGENT_NAME,
            description=AGENT_DESCRIPTION,
            instruction=AGENT_INSTRUCTION,
        )

    async def invoke(self, query: str, session_id: str) -> str:
        """
        Invoke the swap router agent with a query.

        Supports two modes:
        1. Direct mode: Fetches liquidity internally (e.g., "swap 2 million USDT to ETH")
        2. Sequential mode: Accepts pre-fetched liquidity and pool calculator results
           (e.g., "Based on this liquidity data... determine swap amounts")

        Args:
            query: User query or query with pre-fetched data
            session_id: Session ID

        Returns:
            JSON string with routing recommendation
        """
        print(f"🔄 Swap Router Agent received query: {query[:200]}...")

        try:
            # Check if this is sequential mode (has liquidity data in query)
            is_sequential_mode = (
                "liquidity data" in query.lower() or
                "pool calculator" in query.lower() or
                "recommendations" in query.lower()
            )

            if is_sequential_mode:
                # Sequential mode: Extract liquidity data and pool calculator results from query
                print(f"📋 Sequential mode detected - extracting pre-fetched data")
                return await self._invoke_sequential_mode(query, session_id)
            else:
                # Direct mode: Parse query and fetch liquidity internally
                print(f"📋 Direct mode - fetching liquidity internally")
                return await self._invoke_direct_mode(query, session_id)

        except SwapRouterError as e:
            print(f"❌ Swap Router Error: {e}")
            return build_error_response(str(e), getattr(e, "details", {}))
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return build_error_response("internal_error", {"message": str(e)})

    async def _invoke_direct_mode(self, query: str, session_id: str) -> str:
        """Direct mode: Fetch liquidity internally and optimize routing."""
        # Parse query
        params = parse_swap_router_query(query)

        if not params.get("amount"):
            return build_error_response(
                "amount_not_found",
                {"message": "Could not extract swap amount from query"},
            )

        amount = params["amount"]
        token_in = params["token_in"]
        token_out = params["token_out"]
        token_pair = params["token_pair"]

        print(f"📊 Parsed: {amount:,.0f} {token_in} → {token_out}")

        # Fetch liquidity using multichain_liquidity agent
        print(f"🔍 Fetching liquidity for {token_pair}...")
        liquidity_data = await fetch_liquidity_from_multichain_agent(
            token_pair, session_id
        )

        if not liquidity_data or not liquidity_data.get("chains"):
            return build_error_response(
                "liquidity_not_found",
                {"message": f"No liquidity found for {token_pair}"},
            )

        # Convert to PoolData objects
        pools_by_chain = convert_liquidity_to_pool_data(
            liquidity_data, token_in, token_out
        )

        # Check if we have any pools
        total_pools = sum(len(pools) for pools in pools_by_chain.values())
        if total_pools == 0:
            return build_error_response(
                "no_pools_found",
                {"message": f"No matching pools found for {token_pair}"},
            )

        print(f"✅ Found {total_pools} pools across chains")

        # Get optimal allocations from Pool Calculator Agent (LLM reasoning)
        print(f"🧮 Getting optimal allocations from Pool Calculator Agent...")
        optimal_allocations = await get_optimal_allocations_from_pool_calculator(
            liquidity_data=liquidity_data,
            total_amount=amount,
            token_in=token_in,
            token_out=token_out,
            session_id=session_id,
        )
        
        if optimal_allocations and optimal_allocations.get("recommended_allocations"):
            # Use allocations from Pool Calculator
            print(f"✅ Received optimal allocations from Pool Calculator")
            recommended = optimal_allocations["recommended_allocations"]
            print(f"  Allocations: {recommended}")
            
            # Build routes using the recommended allocations
            recommendation = optimize_routing(
                total_amount=amount,
                token_in=token_in,
                token_out=token_out,
                pools_by_chain=pools_by_chain,
                preferred_allocations=recommended,
            )
        else:
            # Fallback to default optimization if Pool Calculator fails
            print(f"⚠️  Pool Calculator did not return valid allocations, using default optimization")
            recommendation = optimize_routing(
                total_amount=amount,
                token_in=token_in,
                token_out=token_out,
                pools_by_chain=pools_by_chain,
            )

        print(f"✅ Routing optimized: {len(recommendation.routes)} routes")

        # Build and return response
        return build_routing_response(recommendation)

    async def _invoke_sequential_mode(self, query: str, session_id: str) -> str:
        """Sequential mode: Use pre-fetched liquidity and pool calculator results."""
        import json
        import re

        # Parse query to extract amount, tokens, liquidity data, and allocations
        params = parse_swap_router_query(query)
        
        if not params.get("amount"):
            return build_error_response(
                "amount_not_found",
                {"message": "Could not extract swap amount from query"},
            )

        amount = params["amount"]
        token_in = params["token_in"]
        token_out = params["token_out"]

        print(f"📊 Sequential mode - Parsed: {amount:,.0f} {token_in} → {token_out}")

        # Try to extract liquidity data from query (may be in JSON format)
        liquidity_data = None
        optimal_allocations = None

        # Look for JSON in the query
        json_match = re.search(r'\{.*\}', query, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                if "chains" in data or "type" in data:
                    liquidity_data = data
                    print(f"✅ Extracted liquidity data from query")
            except json.JSONDecodeError:
                pass

        # Try to extract pool calculator recommendations
        if "recommended_allocations" in query.lower() or "allocations" in query.lower():
            alloc_match = re.search(r'"recommended_allocations"\s*:\s*\{[^}]+\}', query)
            if alloc_match:
                try:
                    alloc_str = "{" + alloc_match.group(0).split("{", 1)[1]
                    alloc_data = json.loads(alloc_str)
                    optimal_allocations = alloc_data
                    print(f"✅ Extracted pool calculator allocations from query")
                except (json.JSONDecodeError, IndexError):
                    pass

        # If liquidity data not found in query, try to parse from text
        if not liquidity_data:
            # The orchestrator should pass liquidity data, but if not, we'll need to fetch it
            print(f"⚠️  Liquidity data not found in query, attempting to fetch...")
            token_pair = f"{token_in}/{token_out}"
            liquidity_data = await fetch_liquidity_from_multichain_agent(
                token_pair, session_id
            )

        if not liquidity_data or not liquidity_data.get("chains"):
            return build_error_response(
                "liquidity_not_found",
                {"message": f"No liquidity data available"},
            )

        # Convert to PoolData objects
        pools_by_chain = convert_liquidity_to_pool_data(
            liquidity_data, token_in, token_out
        )

        # Filter out chains with no pools (skip them)
        pools_by_chain = {chain: pools for chain, pools in pools_by_chain.items() if pools}
        
        if not pools_by_chain:
            return build_error_response(
                "no_pools_found",
                {"message": f"No pools available on any chain for {token_in}/{token_out}"},
            )

        print(f"✅ Found pools on {len(pools_by_chain)} chain(s): {list(pools_by_chain.keys())}")
        total_pools = sum(len(pools) for pools in pools_by_chain.values())
        print(f"   Total pools: {total_pools}")

        # Use optimal allocations if provided, otherwise optimize
        if optimal_allocations and optimal_allocations.get("recommended_allocations"):
            recommended = optimal_allocations["recommended_allocations"]
            # Filter to only chains that have pools
            recommended = {k: v for k, v in recommended.items() if k in pools_by_chain}
            print(f"✅ Using pool calculator allocations: {recommended}")
            recommendation = optimize_routing(
                total_amount=amount,
                token_in=token_in,
                token_out=token_out,
                pools_by_chain=pools_by_chain,
                preferred_allocations=recommended,
            )
        else:
            print(f"📊 Optimizing routing without pool calculator allocations")
            recommendation = optimize_routing(
                total_amount=amount,
                token_in=token_in,
                token_out=token_out,
                pools_by_chain=pools_by_chain,
            )

        print(f"✅ Routing optimized: {len(recommendation.routes)} routes")
        print(f"   Chains used: {[r.chain for r in recommendation.routes]}")

        # Build and return response
        return build_routing_response(recommendation)
