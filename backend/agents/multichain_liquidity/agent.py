"""
Multi-Chain Liquidity Agent Definition

A unified agent that fetches liquidity sequentially from multiple chains.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService

# Import liquidity tools from shared blockchain module
from lib.shared.blockchain.liquidity import (
    get_liquidity_polygon,
    get_liquidity_hedera,
    get_liquidity_ethereum,
)

from .core.constants import (
    DEFAULT_USER_ID,
    AGENT_NAME,
    AGENT_DESCRIPTION,
    get_model_name,
    check_api_keys,
)
from .core.agent_instruction import AGENT_INSTRUCTION
from .services.query_parser import parse_query
from .services.result_combiner import combine_results
from .core.response_validator import (
    validate_and_serialize_response,
    build_error_response,
)


class MultiChainLiquidityAgent:
    """Agent that retrieves liquidity from multiple chains sequentially."""

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
            tools=[
                get_liquidity_hedera,
                get_liquidity_polygon,
                get_liquidity_ethereum,
            ],
        )

    async def invoke(self, query: str, session_id: str) -> str:
        """
        Invoke the multi-chain liquidity agent with a query.

        Args:
            query: User query (e.g., "Get liquidity for ETH/USDT" or "Get liquidity on Polygon")
            session_id: Session ID

        Returns:
            JSON string with liquidity data
        """
        print(f"💧 Multi-Chain Liquidity Agent received query: {query}")

        try:
            # Parse query to extract token pair and chain
            parsed = parse_query(query)
            token_pair = parsed.get("token_pair")
            chain = parsed.get("chain")

            # Determine which chains to query
            chains_to_query = []
            if chain == "hedera":
                chains_to_query = ["hedera"]
            elif chain == "polygon":
                chains_to_query = ["polygon"]
            elif chain == "ethereum":
                chains_to_query = ["ethereum"]
            else:
                # Default: query all chains
                chains_to_query = ["hedera", "polygon", "ethereum"]

            print(f"📊 Querying chains: {chains_to_query}")
            if token_pair:
                print(f"🔍 Token pair: {token_pair}")

            # Fetch liquidity sequentially from each chain by calling tools directly
            hedera_result = None
            polygon_result = None
            ethereum_result = None

            # Query Hedera
            if "hedera" in chains_to_query:
                try:
                    print("🔍 Fetching liquidity from Hedera...")
                    if token_pair:
                        # Hedera function takes a single token address/symbol
                        base, quote = token_pair.split("/")
                        hedera_result = get_liquidity_hedera(base)
                    else:
                        hedera_result = get_liquidity_hedera("")
                    print(
                        f"✅ Hedera: Found {len(hedera_result.get('pools', [])) if isinstance(hedera_result, dict) else 0} pools"
                    )
                except Exception as e:
                    print(f"⚠️  Error fetching Hedera liquidity: {e}")
                    hedera_result = None

            # Query Polygon
            if "polygon" in chains_to_query:
                try:
                    print("🔍 Fetching liquidity from Polygon...")
                    if token_pair:
                        # Polygon function expects token pair string like "ETH/USDT"
                        polygon_result = get_liquidity_polygon(token_pair)
                    else:
                        polygon_result = get_liquidity_polygon("")
                    print(
                        f"✅ Polygon: Found {len(polygon_result.get('pools', [])) if isinstance(polygon_result, dict) else 0} pools"
                    )
                except Exception as e:
                    print(f"⚠️  Error fetching Polygon liquidity: {e}")
                    polygon_result = None

            # Query Ethereum
            if "ethereum" in chains_to_query:
                try:
                    print("🔍 Fetching liquidity from Ethereum...")
                    if token_pair:
                        # Ethereum function expects token pair string like "ETH/USDT"
                        ethereum_result = get_liquidity_ethereum(token_pair)
                    else:
                        ethereum_result = get_liquidity_ethereum("")
                    print(
                        f"✅ Ethereum: Found {len(ethereum_result.get('pools', [])) if isinstance(ethereum_result, dict) else 0} pools"
                    )
                except Exception as e:
                    print(f"⚠️  Error fetching Ethereum liquidity: {e}")
                    ethereum_result = None

            # Combine results
            combined_data = combine_results(
                token_pair=token_pair,
                chain=chain,
                hedera_result=hedera_result,
                polygon_result=polygon_result,
                ethereum_result=ethereum_result,
            )

            response = validate_and_serialize_response(combined_data)
            print(
                f"✅ Successfully combined liquidity data from {len(chains_to_query)} chain(s)"
            )
            return response

        except Exception as e:
            print(f"❌ Error in invoke: {e}")
            import traceback

            traceback.print_exc()
            return build_error_response(str(e))
