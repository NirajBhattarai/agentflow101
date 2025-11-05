"""
Balance Agent (ADK + A2A Protocol)

This agent retrieves account balance information from multiple blockchain chains.
It exposes an A2A Protocol endpoint so it can be called by the orchestrator.
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
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService  # noqa: E402
from google.adk.artifacts import InMemoryArtifactService  # noqa: E402

from .tools import (  # noqa: E402
    get_balance_polygon,
    get_balance_hedera,
    get_balance_all_chains,
    log_message,
)


class TokenBalance(BaseModel):
    token_type: str = Field(description="Type: 'native' or 'token'")
    token_symbol: str = Field(description="Token symbol (e.g., HBAR, USDC)")
    token_address: str = Field(description="Token address")
    balance: str = Field(description="Balance in human-readable format")
    balance_raw: str = Field(description="Raw balance value")
    decimals: int = Field(description="Token decimals")
    error: Optional[str] = Field(default=None, description="Error message if any")


class StructuredBalance(BaseModel):
    type: str = Field(default="balance", description="Response type")
    chain: str = Field(description="Chain name: polygon, hedera, or all")
    account_address: str = Field(description="Account address queried")
    balances: list[TokenBalance] = Field(description="List of token balances")
    total_usd_value: str = Field(description="Total USD value estimate")
    error: Optional[str] = Field(default=None, description="Error message if any")


class BalanceAgent:
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
            print("⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY")

        return LlmAgent(
            model=model_name,
            name="balance_agent",
            description="An agent that retrieves account balance information from multiple blockchain chains including Polygon and Hedera",
            instruction="""
You are a blockchain balance query agent. Your role is to retrieve account balance information from different blockchain chains.

When you receive a balance query request, analyze:
- The account address (Hedera format: 0.0.123456 or EVM format: 0x...)
- The chain to query (polygon, hedera, or all)
- Optional token address/symbol to filter

Use the available tools to fetch balance information:
- get_balance_polygon: For Polygon chain queries
- get_balance_hedera: For Hedera chain queries
- get_balance_all_chains: For cross-chain queries

After fetching the data, return a structured JSON response with this format:
{
  "type": "balance",
  "chain": "polygon | hedera | all",
  "account_address": "0x... or 0.0.123456",
  "balances": [
    {
      "token_type": "native",
      "token_symbol": "HBAR",
      "token_address": "0.0.0",
      "balance": "100.0",
      "balance_raw": "10000000000",
      "decimals": 8
    },
    {
      "token_type": "token",
      "token_symbol": "USDC",
      "token_address": "0.0.123456",
      "balance": "1000.0",
      "balance_raw": "1000000000",
      "decimals": 6
    }
  ],
  "total_usd_value": "$1,100.00"
}

Always use the tools to fetch real data. Return ONLY valid JSON, no markdown code blocks, no other text.
            """,
            tools=[
                get_balance_polygon,
                get_balance_hedera,
                get_balance_all_chains,
                log_message,
            ],
        )

    async def invoke(self, query: str, session_id: str) -> str:
        # HARDCODED RESPONSE FOR TESTING
        # TODO: Replace with actual agent execution once connection issues are resolved

        print(f"🔍 Balance Agent received query: {query}")

        # Parse query to extract account address and chain
        account_address = "0.0.123456"  # Default
        chain = "hedera"  # Default

        if "0.0." in query or "0x" in query.lower():
            # Extract account address
            hedera_match = re.search(r"0\.0\.\d+", query)
            evm_match = re.search(r"0x[a-fA-F0-9]{40}", query)
            if hedera_match:
                account_address = hedera_match.group()
                chain = "hedera"
            elif evm_match:
                account_address = evm_match.group()
                chain = "polygon"

        if "polygon" in query.lower():
            chain = "polygon"
        elif "hedera" in query.lower():
            chain = "hedera"
        elif "all" in query.lower():
            chain = "all"

        # Construct response based on chain: remote for Polygon, hardcoded for Hedera
        if chain == "polygon":
            # Fetch real Polygon balances using the tool
            polygon_result = get_balance_polygon(account_address)
            hardcoded_balance = {
                "type": "balance",
                "chain": "polygon",
                "account_address": polygon_result.get("account_address", account_address),
                "balances": polygon_result.get("balances", []),
                "total_usd_value": polygon_result.get("total_usd_value", "$0.00"),
            }
        elif chain == "hedera":
            # Fetch real Hedera balances using the tool (Mirror Node)
            hedera_result = get_balance_hedera(account_address)
            hardcoded_balance = {
                "type": "balance",
                "chain": "hedera",
                "account_address": hedera_result.get("account_address", account_address),
                "balances": hedera_result.get("balances", []),
                "total_usd_value": hedera_result.get("total_usd_value", "$0.00"),
            }
        elif chain == "all":
            # Fetch both chains remotely and flatten
            polygon_result = get_balance_polygon(account_address)
            hedera_result = get_balance_hedera(account_address)
            polygon_balances = [
                {**b, "chain": "polygon"} for b in polygon_result.get("balances", [])
            ]
            hedera_balances = [
                {**b, "chain": "hedera"} for b in hedera_result.get("balances", [])
            ]

            hardcoded_balance = {
                "type": "balance",
                "chain": "all",
                "account_address": account_address,
                "balances": [*hedera_balances, *polygon_balances],
                "total_usd_value": "$0.00",
            }
        else:
            # Default to Hedera hardcoded if chain is unknown
            hardcoded_balance = {
                "type": "balance",
                "chain": chain,
                "account_address": account_address,
                "balances": [],
                "total_usd_value": "$0.00",
            }

        # no post-processing override; return as built above

        try:
            # Validate and return the response
            validated_balance = StructuredBalance(**hardcoded_balance)
            final_response = json.dumps(validated_balance.model_dump(), indent=2)

            print(
                f"✅ Returning hardcoded balance response for {account_address} on {chain}"
            )
            print(f"📦 Response length: {len(final_response)} chars")
            print(f"📄 Response preview: {final_response[:200]}...")

            # Ensure the response is valid JSON
            json.loads(final_response)  # Validate it's parseable

            return final_response
        except Exception as e:
            print(f"❌ Validation error: {e}")
            error_response = json.dumps(
                {
                    "type": "balance",
                    "chain": chain,
                    "account_address": account_address,
                    "balances": [],
                    "total_usd_value": "$0.00",
                    "error": f"Validation failed: {str(e)}",
                },
                indent=2,
            )
            return error_response


class BalanceExecutor(AgentExecutor):
    def __init__(self):
        self.agent = BalanceAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = context.get_user_input()
        session_id = getattr(context, "context_id", "default_session")

        try:
            final_content = await self.agent.invoke(query, session_id)

            # Validate that final_content is not empty
            if not final_content or not final_content.strip():
                print("⚠️  Warning: Empty response from agent, using fallback")
                final_content = json.dumps(
                    {
                        "type": "balance",
                        "chain": "unknown",
                        "account_address": "unknown",
                        "balances": [],
                        "total_usd_value": "$0.00",
                        "error": "Empty response from agent",
                    },
                    indent=2,
                )

            # Ensure it's valid JSON
            try:
                json.loads(final_content)  # Validate it's parseable
                print(f"✅ Validated JSON response: {len(final_content)} chars")
            except json.JSONDecodeError as e:
                print(f"⚠️  Warning: Response is not valid JSON: {e}")
                print(f"Response content (first 500 chars): {final_content[:500]}")
                # Wrap it in a JSON structure
                final_content = json.dumps(
                    {
                        "type": "balance",
                        "chain": "unknown",
                        "account_address": "unknown",
                        "balances": [],
                        "total_usd_value": "$0.00",
                        "error": f"Invalid JSON response: {str(e)}",
                        "raw_response": final_content[:500],
                    },
                    indent=2,
                )

            print(f"📤 Sending response to event queue: {len(final_content)} chars")
            print(f"📄 First 100 chars: {final_content[:100]}")

            # Send the message
            await event_queue.enqueue_event(new_agent_text_message(final_content))
            print("✅ Successfully enqueued response")

        except Exception as e:
            print(f"❌ Error in execute: {e}")
            import traceback

            traceback.print_exc()
            error_response = json.dumps(
                {
                    "type": "balance",
                    "chain": "unknown",
                    "account_address": "unknown",
                    "balances": [],
                    "total_usd_value": "$0.00",
                    "error": f"Execution error: {str(e)}",
                },
                indent=2,
            )
            await event_queue.enqueue_event(new_agent_text_message(error_response))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")
