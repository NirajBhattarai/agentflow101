"""
Parallel Liquidity Agent (ADK + A2A Protocol)

This is a completely independent agent that retrieves liquidity information
from multiple blockchain chains in parallel using ParallelAgent.
When given a token pair like "ETH/USDT", it fetches liquidity from both
Hedera (SaucerSwap) and Polygon simultaneously.
"""

import os
import json
import re
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# A2A Protocol imports
from a2a.server.agent_execution import AgentExecutor, RequestContext  # noqa: E402
from a2a.server.events import EventQueue  # noqa: E402
from a2a.utils import new_agent_text_message  # noqa: E402

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

# Import liquidity tools from liquidity agent
from ...liquidity.tools import (  # noqa: E402
    get_liquidity_polygon,
    get_liquidity_hedera,
)

# Import independent sub-agents
from .hedera_liquidity_agent import build_hedera_liquidity_agent  # noqa: E402
from .polygon_liquidity_agent import build_polygon_liquidity_agent  # noqa: E402


class LiquidityPair(BaseModel):
    base: str = Field(description="Base token symbol")
    quote: str = Field(description="Quote token symbol")
    pool_address: str = Field(description="Pool contract address")
    dex: str = Field(description="DEX name (e.g., SaucerSwap, HeliSwap, QuickSwap)")
    tvl_usd: float = Field(description="Total Value Locked in USD")
    reserve_base: float = Field(description="Base token reserve")
    reserve_quote: float = Field(description="Quote token reserve")
    fee_bps: int = Field(description="Fee in basis points")
    chain: str = Field(description="Chain name: polygon or hedera")


class StructuredParallelLiquidity(BaseModel):
    type: str = Field(default="parallel_liquidity", description="Response type")
    token_pair: str = Field(description="Token pair queried (e.g., ETH/USDT)")
    chains: dict = Field(description="Liquidity data by chain")
    hedera_pairs: list[LiquidityPair] = Field(
        default=[], description="Hedera liquidity pairs"
    )
    polygon_pairs: list[LiquidityPair] = Field(
        default=[], description="Polygon liquidity pairs"
    )
    all_pairs: list[LiquidityPair] = Field(
        default=[], description="All liquidity pairs combined"
    )
    error: Optional[str] = Field(default=None, description="Error message if any")


class ParallelLiquidityAgent:
    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = "remote_agent"
        # Store session service reference separately for session management
        self._session_service = InMemorySessionService()
        # Use "agents" as app_name to match where ParallelAgent sub-agents are loaded from
        # (google.adk.agents package)
        self._runner = Runner(
            app_name="agents",  # Must match the directory where agents are loaded from
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=self._session_service,
            memory_service=InMemoryMemoryService(),
        )

    def _build_agent(self):
        """Build parallel agent with sub-agents for Hedera and Polygon."""
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
            print("⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY")

        # If ParallelAgent is not available, fall back to sequential agent
        if ParallelAgent is None:
            print("⚠️  ParallelAgent not available, using sequential LlmAgent")
            return LlmAgent(
                model=model_name,
                name="parallel_liquidity_agent",
                description="Agent that retrieves liquidity from Hedera and Polygon (sequential fallback)",
                instruction="""
                You are a liquidity query agent. When given a token pair like "ETH/USDT",
                fetch liquidity from both Hedera and Polygon chains.
                Use get_liquidity_hedera for Hedera and get_liquidity_polygon for Polygon.
                Return combined results in JSON format.
                """,
                tools=[get_liquidity_hedera, get_liquidity_polygon],
            )

        # Import and build independent sub-agents
        hedera_agent = build_hedera_liquidity_agent()
        polygon_agent = build_polygon_liquidity_agent()

        # Create parallel agent that runs both sub-agents concurrently
        parallel_agent = ParallelAgent(
            name="ParallelLiquidityAgent",
            sub_agents=[hedera_agent, polygon_agent],
            description="Fetches liquidity from Hedera and Polygon chains in parallel",
        )

        return parallel_agent

    async def invoke(self, query: str, session_id: str) -> str:
        """Invoke the parallel liquidity agent."""
        print(f"💧🚀 Parallel Liquidity Agent received query: {query}")

        # Parse token pair from query
        token_pair = self._extract_token_pair(query)
        if not token_pair:
            return json.dumps(
                {
                    "type": "parallel_liquidity",
                    "token_pair": "",
                    "chains": {},
                    "hedera_pairs": [],
                    "polygon_pairs": [],
                    "all_pairs": [],
                    "error": "Could not extract token pair from query. Please provide format like 'ETH/USDT' or 'HBAR/USDC'",
                },
                indent=2,
            )

        print(f"📊 Extracted token pair: {token_pair}")

        # If ParallelAgent is not available, use sequential fallback
        if ParallelAgent is None:
            return await self._invoke_sequential(query, token_pair, session_id)

        try:
            # Execute parallel agent
            formatted_query = f"Get liquidity for {token_pair}"

            print(f"🚀 Executing parallel liquidity fetch for {token_pair}...")
            print(f"   Query: {formatted_query}")
            print(f"   User ID: {self._user_id}")
            print(f"   Session ID: {session_id}")

            # Ensure session exists before calling run_async
            # The Runner requires the session to exist in the session service
            print("   Checking/creating session...")
            try:
                existing_session = await self._session_service.get_session(
                    app_name="agents",
                    user_id=self._user_id,
                    session_id=session_id,
                )
                if existing_session is None:
                    print("   Session not found, creating new session...")
                    await self._session_service.create_session(
                        app_name="agents",
                        user_id=self._user_id,
                        session_id=session_id,
                    )
                    print("   ✅ Session created successfully")
                else:
                    print("   ✅ Session already exists")
            except Exception as e_session:
                print(f"   ⚠️  Error checking/creating session: {e_session}")
                # Try to create anyway
                try:
                    await self._session_service.create_session(
                        app_name="agents",
                        user_id=self._user_id,
                        session_id=session_id,
                    )
                    print("   ✅ Session created after error")
                except Exception as e_create:
                    print(f"   ⚠️  Failed to create session: {e_create}")
                    # Will fail in run_async if session can't be created

            # Use the correct Runner.run_async API signature
            # API: run_async(*, user_id, session_id, new_message: Optional[Content] = None, ...)
            # Returns: AsyncGenerator[Event, None]
            print("   Using correct Runner.run_async API with new_message parameter...")

            # Create Content object with Part containing the message
            message_content = Content(parts=[Part(text=formatted_query)])

            print(f"   Created Content object with message: {formatted_query}")

            # Call run_async - it returns an AsyncGenerator, so we need to iterate through events
            event_generator = self._runner.run_async(
                user_id=self._user_id,
                session_id=session_id,
                new_message=message_content,
            )

            print(
                "   ✅ Runner.run_async called successfully, iterating through events..."
            )

            # Iterate through events to get the final result
            final_state = None
            async for event in event_generator:
                # Check if event has state
                if hasattr(event, "state") and event.state:
                    final_state = event.state
                    print(
                        f"   📦 Found state in event: {list(event.state.keys()) if event.state else 'empty'}"
                    )
                # Check if event is a completion event
                if hasattr(event, "type") and "complete" in str(event.type).lower():
                    print(f"   ✅ Received completion event: {event.type}")
                    break

            # Extract results from final state
            result = (
                type("Result", (), {"state": final_state})() if final_state else None
            )

            if not result or not result.state:
                print("   ⚠️  No state found in events, checking last event...")
                # Try to get state from the session service
                try:
                    session = await self._session_service.get_session(
                        app_name="agents",
                        user_id=self._user_id,
                        session_id=session_id,
                    )
                    if session and hasattr(session, "state"):
                        final_state = session.state
                        result = type("Result", (), {"state": final_state})()
                        print(
                            f"   📦 Got state from session: {list(final_state.keys()) if final_state else 'empty'}"
                        )
                except Exception as e_session:
                    print(f"   ⚠️  Could not get state from session: {e_session}")

            print("✅ Parallel execution completed")

            # Extract results from state (stored with output_key)
            hedera_result = None
            polygon_result = None

            # Try to get results from final_state
            if final_state:
                hedera_result = final_state.get("hedera_liquidity")
                polygon_result = final_state.get("polygon_liquidity")
                print(
                    f"📦 State contents: {list(final_state.keys()) if final_state else 'empty'}"
                )
                print(f"   Hedera result found: {hedera_result is not None}")
                print(f"   Polygon result found: {polygon_result is not None}")

                # Also check if results are stored with different keys
                if not hedera_result:
                    # Try alternative keys
                    for key in final_state.keys():
                        if "hedera" in key.lower():
                            hedera_result = final_state.get(key)
                            print(f"   Found Hedera result in key: {key}")
                            break

                if not polygon_result:
                    # Try alternative keys
                    for key in final_state.keys():
                        if "polygon" in key.lower():
                            polygon_result = final_state.get(key)
                            print(f"   Found Polygon result in key: {key}")
                            break

            # If results are strings, try to parse them
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

            # If not in state, use sequential fallback
            if not hedera_result or not polygon_result:
                print(
                    "⚠️  Results not found in state, falling back to sequential execution"
                )
                print(
                    f"   Hedera result: {type(hedera_result).__name__ if hedera_result else 'None'}"
                )
                print(
                    f"   Polygon result: {type(polygon_result).__name__ if polygon_result else 'None'}"
                )
                return await self._invoke_sequential(query, token_pair, session_id)

            print(
                "✅ Successfully retrieved results from both chains via ParallelAgent"
            )
            # Process and combine results
            return self._combine_results(token_pair, hedera_result, polygon_result)

        except TypeError as e:
            # Handle API signature errors
            print(f"⚠️  Runner API error: {e}")
            print("   Falling back to sequential execution")
            return await self._invoke_sequential(query, token_pair, session_id)
        except Exception as e:
            print(f"⚠️  Error in parallel execution: {e}")
            import traceback

            traceback.print_exc()
            # Fallback to sequential
            return await self._invoke_sequential(query, token_pair, session_id)

    def _extract_token_pair(self, query: str) -> Optional[str]:
        """Extract token pair from query (e.g., 'ETH/USDT', 'HBAR/USDC')."""
        if not query:
            return None

        query_upper = query.upper()

        # Pattern to match token pairs: ETH/USDT, HBAR/USDC, etc.
        patterns = [
            r"([A-Z0-9]{2,})/([A-Z0-9]{2,})",  # ETH/USDT, HBAR/USDC
            r"pair[:\s=]+([A-Z0-9]+)/([A-Z0-9]+)",  # pair: ETH/USDT
            r"for\s+([A-Z0-9]+)/([A-Z0-9]+)",  # for ETH/USDT
        ]

        for pattern in patterns:
            match = re.search(pattern, query_upper)
            if match:
                if len(match.groups()) >= 2:
                    return f"{match.group(1)}/{match.group(2)}"
                elif "/" in match.group(0):
                    return match.group(0)

        return None

    async def _invoke_sequential(
        self, query: str, token_pair: str, session_id: str
    ) -> str:
        """Fallback sequential execution when ParallelAgent is not available."""
        print("⚠️  Using sequential fallback (ParallelAgent not available)")

        try:
            # Extract base and quote tokens
            base, quote = token_pair.split("/")

            # Fetch from Hedera
            print(f"🔍 Fetching liquidity from Hedera for {token_pair}...")
            hedera_result = get_liquidity_hedera(base)

            # Fetch from Polygon
            print(f"🔍 Fetching liquidity from Polygon for {token_pair}...")
            polygon_result = get_liquidity_polygon(base)

            return self._combine_results(token_pair, hedera_result, polygon_result)

        except Exception as e:
            print(f"❌ Error in sequential execution: {e}")
            import traceback

            traceback.print_exc()
            return json.dumps(
                {
                    "type": "parallel_liquidity",
                    "token_pair": token_pair,
                    "chains": {},
                    "hedera_pairs": [],
                    "polygon_pairs": [],
                    "all_pairs": [],
                    "error": f"Error fetching liquidity: {str(e)}",
                },
                indent=2,
            )

    def _combine_results(
        self,
        token_pair: str,
        hedera_result: Optional[dict],
        polygon_result: Optional[dict],
    ) -> str:
        """Combine results from Hedera and Polygon into unified response."""
        base, quote = token_pair.split("/")

        hedera_pairs = []
        polygon_pairs = []

        # Process Hedera results
        if hedera_result:
            if isinstance(hedera_result, str):
                try:
                    hedera_result = json.loads(hedera_result)
                except (json.JSONDecodeError, ValueError):
                    pass

            if isinstance(hedera_result, dict):
                pools = hedera_result.get("pools", [])
                for pool in pools:
                    hedera_pairs.append(
                        LiquidityPair(
                            base=base,
                            quote=quote,
                            pool_address=pool.get("pool_address", ""),
                            dex=pool.get("dex", "SaucerSwap"),
                            tvl_usd=self._parse_tvl(pool.get("tvl", "$0")),
                            reserve_base=float(pool.get("liquidity", 0)) / 2,
                            reserve_quote=float(pool.get("liquidity", 0)) / 2,
                            fee_bps=30,  # Default fee for Hedera
                            chain="hedera",
                        )
                    )

        # Process Polygon results
        if polygon_result:
            if isinstance(polygon_result, str):
                try:
                    polygon_result = json.loads(polygon_result)
                except (json.JSONDecodeError, ValueError):
                    pass

            if isinstance(polygon_result, dict):
                pools = polygon_result.get("pools", [])
                for pool in pools:
                    polygon_pairs.append(
                        LiquidityPair(
                            base=base,
                            quote=quote,
                            pool_address=pool.get("pool_address", ""),
                            dex=pool.get("dex", "QuickSwap"),
                            tvl_usd=self._parse_tvl(pool.get("tvl", "$0")),
                            reserve_base=float(pool.get("liquidity", 0)) / 2,
                            reserve_quote=float(pool.get("liquidity", 0)) / 2,
                            fee_bps=25,  # Default fee for Polygon
                            chain="polygon",
                        )
                    )

        # Combine all pairs
        all_pairs = hedera_pairs + polygon_pairs

        # Build response
        response = StructuredParallelLiquidity(
            type="parallel_liquidity",
            token_pair=token_pair,
            chains={
                "hedera": {
                    "pairs": [p.model_dump() for p in hedera_pairs],
                    "total_pools": len(hedera_pairs),
                },
                "polygon": {
                    "pairs": [p.model_dump() for p in polygon_pairs],
                    "total_pools": len(polygon_pairs),
                },
            },
            hedera_pairs=hedera_pairs,
            polygon_pairs=polygon_pairs,
            all_pairs=all_pairs,
        )

        return json.dumps(response.model_dump(), indent=2)

    def _parse_tvl(self, tvl_str: str) -> float:
        """Parse TVL string like '$1,200,000' to float."""
        if isinstance(tvl_str, (int, float)):
            return float(tvl_str)

        if not isinstance(tvl_str, str):
            return 0.0

        # Remove $ and commas
        cleaned = tvl_str.replace("$", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0


class ParallelLiquidityExecutor(AgentExecutor):
    """A2A Protocol executor for parallel liquidity agent."""

    def __init__(self):
        self.agent = ParallelLiquidityAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        session_id = getattr(context, "context_id", "default_session")

        try:
            final_content = await self.agent.invoke(query, session_id)

            if not final_content or not final_content.strip():
                print("⚠️  Warning: Empty response from agent")
                final_content = json.dumps(
                    {
                        "type": "parallel_liquidity",
                        "token_pair": "",
                        "chains": {},
                        "hedera_pairs": [],
                        "polygon_pairs": [],
                        "all_pairs": [],
                        "error": "Empty response from agent",
                    },
                    indent=2,
                )

            # Validate JSON
            try:
                json.loads(final_content)
                print(f"✅ Validated JSON response: {len(final_content)} chars")
            except json.JSONDecodeError as e:
                print(f"⚠️  Warning: Response is not valid JSON: {e}")
                final_content = json.dumps(
                    {
                        "type": "parallel_liquidity",
                        "token_pair": "",
                        "chains": {},
                        "hedera_pairs": [],
                        "polygon_pairs": [],
                        "all_pairs": [],
                        "error": f"Invalid JSON response: {str(e)}",
                    },
                    indent=2,
                )

            print(f"📤 Sending response to event queue: {len(final_content)} chars")
            await event_queue.enqueue_event(new_agent_text_message(final_content))
            print("✅ Successfully enqueued response")

        except Exception as e:
            print(f"❌ Error in execute: {e}")
            import traceback

            traceback.print_exc()
            error_response = json.dumps(
                {
                    "type": "parallel_liquidity",
                    "token_pair": "",
                    "chains": {},
                    "hedera_pairs": [],
                    "polygon_pairs": [],
                    "all_pairs": [],
                    "error": f"Execution error: {str(e)}",
                },
                indent=2,
            )
            await event_queue.enqueue_event(new_agent_text_message(error_response))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")
