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

        Args:
            query: User query (e.g., "swap 2 million USDT to ETH")
            session_id: Session ID

        Returns:
            JSON string with routing recommendation
        """
        print(f"🔄 Swap Router Agent received query: {query}")

        try:
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

        except SwapRouterError as e:
            print(f"❌ Swap Router Error: {e}")
            return build_error_response(str(e), getattr(e, "details", {}))
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback

            traceback.print_exc()
            return build_error_response("internal_error", {"message": str(e)})
