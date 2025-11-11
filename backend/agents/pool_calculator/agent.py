"""
Pool Calculator Agent Definition

An agent that processes liquidity and slot0 data from multiple chains,
analyzes price impacts, and uses LLM to recommend optimal swap routing
across chains.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService

from .core.constants import (
    DEFAULT_USER_ID,
    AGENT_NAME,
    AGENT_DESCRIPTION,
    get_model_name,
    check_api_keys,
)
from .core.agent_instruction import AGENT_INSTRUCTION
from .tools.calculations import (
    calculate_price_from_sqrt_price_x96,
    calculate_swap_output,
    analyze_pool_health,
    process_pool_data,
    prepare_pools_by_chain,
    analyze_price_impact_for_allocation,
)


class PoolCalculatorAgent:
    """Agent that processes pool data and provides calculations with LLM insights."""

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
                prepare_pools_by_chain,
                analyze_price_impact_for_allocation,
                calculate_price_from_sqrt_price_x96,
                calculate_swap_output,
                analyze_pool_health,
                process_pool_data,
            ],
        )

    async def invoke(self, query: str, session_id: str) -> str:
        """
        Invoke the pool calculator agent with a query.

        Args:
            query: User query with pool data or calculation request
            session_id: Session ID

        Returns:
            Natural language response with calculations and insights
        """
        print(f"🧮 Pool Calculator Agent received query: {query}")

        try:
            # Run the agent with the query
            # Note: run_async expects query as positional or keyword 'query', not 'message'
            response = await self._runner.run_async(
                user_id=self._user_id,
                session_id=session_id,
                query=query,
            )

            # Extract text response
            if hasattr(response, "text"):
                return response.text
            elif isinstance(response, str):
                return response
            else:
                return str(response)

        except Exception as e:
            error_msg = f"Error in Pool Calculator Agent: {e}"
            print(f"❌ {error_msg}")
            return f"Error: {error_msg}"

