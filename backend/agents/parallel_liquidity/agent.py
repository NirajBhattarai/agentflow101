"""
Parallel Liquidity Agent Definition

Defines the ParallelLiquidityAgent class that handles parallel liquidity queries.
"""

import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# Google ADK imports
from google.adk.agents.llm_agent import LlmAgent  # noqa: E402
from google.adk.runners import Runner  # noqa: E402
import google.adk.runners as runners_module  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.adk.memory.in_memory_memory_service import (
    InMemoryMemoryService,
)  # noqa: E402
from google.adk.artifacts import InMemoryArtifactService  # noqa: E402

# Get Content and Part from runners.types
Content = runners_module.types.Content  # noqa: E402
Part = runners_module.types.Part  # noqa: E402

# Try to import ParallelAgent - check different possible import paths
try:
    from google.adk.agents.parallel_agent import ParallelAgent  # noqa: E402
except ImportError:
    try:
        from google.adk.workflow.parallel_agent import ParallelAgent  # noqa: E402
    except ImportError:
        try:
            from google.adk.agents import ParallelAgent  # noqa: E402
        except ImportError:
            print("⚠️  Warning: ParallelAgent not found. Using sequential fallback.")
            ParallelAgent = None

# Import liquidity tools from shared blockchain module
from lib.shared.blockchain.liquidity import (  # noqa: E402
    get_liquidity_polygon,
    get_liquidity_hedera,
    get_liquidity_ethereum,
)

# Import independent sub-agents
from .agents.hedera_liquidity_agent import build_hedera_liquidity_agent  # noqa: E402
from .agents.polygon_liquidity_agent import build_polygon_liquidity_agent  # noqa: E402
from .agents.ethereum_liquidity_agent import build_ethereum_liquidity_agent  # noqa: E402

# Import core modules
from .core.constants import (  # noqa: E402
    DEFAULT_USER_ID,
    DEFAULT_APP_NAME,
    AGENT_NAME,
    AGENT_DESCRIPTION,
    SEQUENTIAL_FALLBACK_INSTRUCTION,
    OUTPUT_KEY_HEDERA,
    OUTPUT_KEY_POLYGON,
    OUTPUT_KEY_ETHEREUM,
    get_model_name,
    check_api_keys,
    ERROR_TOKEN_PAIR_NOT_FOUND,
)
from .core.response_validator import (  # noqa: E402
    build_error_response,
    validate_and_serialize_response,
    log_response_info,
)
from .services.query_parser import extract_token_pair  # noqa: E402
from .services.result_combiner import combine_results  # noqa: E402


def _get_parallel_agent():
    """Get ParallelAgent if available."""
    return ParallelAgent


def _build_sequential_agent(model_name: str) -> LlmAgent:
    """Build sequential fallback agent."""
    print("⚠️  ParallelAgent not available, using sequential LlmAgent")
    return LlmAgent(
        model=model_name,
        name="parallel_liquidity_agent",
        description="Agent that retrieves liquidity from Hedera, Polygon, and Ethereum (sequential fallback)",
        instruction=SEQUENTIAL_FALLBACK_INSTRUCTION,
        tools=[get_liquidity_hedera, get_liquidity_polygon, get_liquidity_ethereum],
    )


def _build_parallel_agent(model_name: str) -> ParallelAgent:
    """Build parallel agent with sub-agents."""
    hedera_agent = build_hedera_liquidity_agent()
    polygon_agent = build_polygon_liquidity_agent()
    ethereum_agent = build_ethereum_liquidity_agent()
    return ParallelAgent(
        name=AGENT_NAME,
        sub_agents=[hedera_agent, polygon_agent, ethereum_agent],
        description=AGENT_DESCRIPTION,
    )


async def _ensure_session(
    session_service, app_name: str, user_id: str, session_id: str
):
    """Ensure session exists in session service."""
    try:
        existing_session = await session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )
        if existing_session is None:
            await session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
            )
    except Exception:
        try:
            await session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
            )
        except Exception:
            pass


def _extract_results_from_state(
    final_state: dict,
) -> tuple[Optional[dict], Optional[dict], Optional[dict]]:
    """Extract Hedera, Polygon, and Ethereum results from state."""
    hedera_result = final_state.get(OUTPUT_KEY_HEDERA)
    polygon_result = final_state.get(OUTPUT_KEY_POLYGON)
    ethereum_result = final_state.get(OUTPUT_KEY_ETHEREUM)

    if not hedera_result:
        for key in final_state.keys():
            if "hedera" in key.lower():
                hedera_result = final_state.get(key)
                break

    if not polygon_result:
        for key in final_state.keys():
            if "polygon" in key.lower():
                polygon_result = final_state.get(key)
                break

    if not ethereum_result:
        for key in final_state.keys():
            if "ethereum" in key.lower() or "eth" in key.lower():
                ethereum_result = final_state.get(key)
                break

    # Parse JSON strings if needed
    if isinstance(hedera_result, str):
        try:
            hedera_result = json.loads(hedera_result)
        except (json.JSONDecodeError, ValueError):
            pass

    if isinstance(polygon_result, str):
        try:
            polygon_result = json.loads(polygon_result)
        except (json.JSONDecodeError, ValueError):
            pass

    if isinstance(ethereum_result, str):
        try:
            ethereum_result = json.loads(ethereum_result)
        except (json.JSONDecodeError, ValueError):
            pass

    return hedera_result, polygon_result, ethereum_result


class ParallelLiquidityAgent:
    """Agent that retrieves liquidity from multiple chains in parallel."""

    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = DEFAULT_USER_ID
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            app_name=DEFAULT_APP_NAME,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=self._session_service,
            memory_service=InMemoryMemoryService(),
        )

    def _build_agent(self):
        """Build parallel agent with sub-agents for Hedera and Polygon."""
        model_name = get_model_name()
        check_api_keys()

        parallel_agent_class = _get_parallel_agent()
        if parallel_agent_class is None:
            return _build_sequential_agent(model_name)

        return _build_parallel_agent(model_name)

    async def invoke(self, query: str, session_id: str) -> str:
        """Invoke the parallel liquidity agent."""
        print(f"💧🚀 Parallel Liquidity Agent received query: {query}")

        token_pair = extract_token_pair(query)
        if not token_pair:
            return build_error_response("", ERROR_TOKEN_PAIR_NOT_FOUND)

        print(f"📊 Extracted token pair: {token_pair}")

        parallel_agent_class = _get_parallel_agent()
        if parallel_agent_class is None:
            return await self._invoke_sequential(query, token_pair, session_id)

        try:
            return await self._invoke_parallel(query, token_pair, session_id)
        except Exception as e:
            print(f"⚠️  Error in parallel execution: {e}")
            import traceback

            traceback.print_exc()
            return await self._invoke_sequential(query, token_pair, session_id)

    async def _invoke_parallel(
        self, query: str, token_pair: str, session_id: str
    ) -> str:
        """Execute parallel agent."""
        formatted_query = f"Get liquidity for {token_pair}"
        print(f"🚀 Executing parallel liquidity fetch for {token_pair}...")

        await _ensure_session(
            self._session_service,
            DEFAULT_APP_NAME,
            self._user_id,
            session_id,
        )

        message_content = Content(parts=[Part(text=formatted_query)])
        event_generator = self._runner.run_async(
            user_id=self._user_id,
            session_id=session_id,
            new_message=message_content,
        )

        final_state = None
        async for event in event_generator:
            if hasattr(event, "state") and event.state:
                final_state = event.state
            if hasattr(event, "type") and "complete" in str(event.type).lower():
                break

        if not final_state:
            session = await self._session_service.get_session(
                app_name=DEFAULT_APP_NAME,
                user_id=self._user_id,
                session_id=session_id,
            )
            if session and hasattr(session, "state"):
                final_state = session.state

        hedera_result, polygon_result, ethereum_result = _extract_results_from_state(final_state or {})

        # At least one chain should have results
        if not hedera_result and not polygon_result and not ethereum_result:
            print("⚠️  Results not found in state, falling back to sequential execution")
            return await self._invoke_sequential(query, token_pair, session_id)

        print("✅ Successfully retrieved results from chains via ParallelAgent")
        combined_data = combine_results(token_pair, hedera_result, polygon_result, ethereum_result)
        response = validate_and_serialize_response(combined_data)
        log_response_info(token_pair, response)
        return response

    async def _invoke_sequential(
        self, query: str, token_pair: str, session_id: str
    ) -> str:
        """Fallback sequential execution when ParallelAgent is not available."""
        print("⚠️  Using sequential fallback (ParallelAgent not available)")

        try:
            base, quote = token_pair.split("/")
            print(f"🔍 Fetching liquidity from Hedera for {token_pair}...")
            hedera_result = get_liquidity_hedera(base)
            print(f"🔍 Fetching liquidity from Polygon for {token_pair}...")
            # Pass full token pair to get liquidity and slot0 from pool
            polygon_result = get_liquidity_polygon(token_pair)
            print(f"🔍 Fetching liquidity from Ethereum for {token_pair}...")
            # Pass full token pair to get liquidity and slot0 from pool
            ethereum_result = get_liquidity_ethereum(token_pair)

            combined_data = combine_results(token_pair, hedera_result, polygon_result, ethereum_result)
            response = validate_and_serialize_response(combined_data)
            log_response_info(token_pair, response)
            return response
        except Exception as e:
            print(f"❌ Error in sequential execution: {e}")
            import traceback

            traceback.print_exc()

            return build_error_response(
                token_pair, f"Error fetching liquidity: {str(e)}"
            )
