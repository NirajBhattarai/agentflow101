"""
Liquidity Agent (ADK + A2A Protocol)

This agent retrieves liquidity information from multiple blockchain chains.
It exposes an A2A Protocol endpoint so it can be called by the orchestrator.
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# A2A Protocol imports
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

# Google ADK imports
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types

from .tools import (
    get_liquidity_polygon,
    get_liquidity_hedera,
    get_liquidity_all_chains,
    log_message,
)


class LiquidityPair(BaseModel):
    base: str = Field(description="Base token symbol")
    quote: str = Field(description="Quote token symbol")
    pool_address: str = Field(description="Pool contract address")
    dex: str = Field(description="DEX name (e.g., SaucerSwap, HeliSwap)")
    tvl_usd: float = Field(description="Total Value Locked in USD")
    reserve_base: float = Field(description="Base token reserve")
    reserve_quote: float = Field(description="Quote token reserve")
    fee_bps: int = Field(description="Fee in basis points")


class StructuredLiquidity(BaseModel):
    type: str = Field(default="liquidity", description="Response type")
    chain: str = Field(description="Chain name: polygon, hedera, or all")
    pairs: list[LiquidityPair] = Field(description="List of liquidity pairs")
    error: Optional[str] = Field(default=None, description="Error message if any")


class LiquidityAgent:
    def __init__(self):
        self._agent = self._build_agent()
        self._user_id = "remote_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def _build_agent(self) -> LlmAgent:
        # Use native Gemini model directly
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        # Fallback to GOOGLE_API_KEY if GEMINI_MODEL not set
        if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
            print(
                "⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY"
            )

        return LlmAgent(
            model=model_name,
            name="liquidity_agent",
            description="An agent that retrieves liquidity information from multiple blockchain chains including Polygon and Hedera",
            instruction="""
You are a blockchain liquidity query agent. Your role is to retrieve liquidity pool information from different blockchain chains.

When you receive a liquidity query request, analyze:
- The chain to query (polygon, hedera, or all)
- Optional token pairs to filter (e.g., HBAR/USDC)

Use the available tools to fetch liquidity information:
- get_liquidity_polygon: For Polygon chain queries
- get_liquidity_hedera: For Hedera chain queries
- get_liquidity_all_chains: For cross-chain queries

After fetching the data, return a structured JSON response with this format:
{
  "type": "liquidity",
  "chain": "polygon | hedera | all",
  "pairs": [
    {
      "base": "HBAR",
      "quote": "USDC",
      "pool_address": "0x... or 0.0.123456",
      "dex": "SaucerSwap",
      "tvl_usd": 1000000.0,
      "reserve_base": 500000.0,
      "reserve_quote": 500000.0,
      "fee_bps": 30
    }
  ]
}

Always use the tools to fetch real data. Return ONLY valid JSON, no markdown code blocks, no other text.
            """,
            tools=[
                get_liquidity_polygon,
                get_liquidity_hedera,
                get_liquidity_all_chains,
                log_message,
            ],
        )

    async def invoke(self, query: str, session_id: str) -> str:
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )

        content = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )

        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )

        response_text = ""
        async for event in self._runner.run_async(
            user_id=self._user_id,
            session_id=session.id,
            new_message=content,
        ):
            if event.is_final_response():
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    response_text = "\n".join(
                        [p.text for p in event.content.parts if p.text]
                    )
                break

        content_str = response_text.strip()

        # Extract JSON from markdown code blocks if present
        if "```json" in content_str:
            content_str = content_str.split("```json")[1].split("```")[0].strip()
        elif "```" in content_str:
            content_str = content_str.split("```")[1].split("```")[0].strip()

        try:
            structured_data = json.loads(content_str)
            validated_liquidity = StructuredLiquidity(**structured_data)
            final_response = json.dumps(validated_liquidity.model_dump(), indent=2)
            print("✅ Successfully created structured liquidity response")
            return final_response
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Content: {content_str[:500]}")
            return json.dumps(
                {
                    "type": "liquidity",
                    "chain": "unknown",
                    "pairs": [],
                    "error": f"Failed to parse JSON: {str(e)}",
                    "raw_content": content_str[:200],
                }
            )
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return json.dumps(
                {
                    "type": "liquidity",
                    "chain": "unknown",
                    "pairs": [],
                    "error": f"Validation failed: {str(e)}",
                }
            )


class LiquidityExecutor(AgentExecutor):
    def __init__(self):
        self.agent = LiquidityAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        session_id = getattr(context, "context_id", "default_session")
        final_content = await self.agent.invoke(query, session_id)
        await event_queue.enqueue_event(new_agent_text_message(final_content))

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception("cancel not supported")
