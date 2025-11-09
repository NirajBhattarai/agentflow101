"""
Bridge Agent (ADK + A2A Protocol)

This agent handles token bridging across blockchain chains.
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


class BridgeTransaction(BaseModel):
    source_chain: str = Field(description="Source chain (hedera or polygon)")
    destination_chain: str = Field(description="Destination chain (hedera or polygon)")
    token_symbol: str = Field(description="Token symbol (e.g., HBAR, USDC)")
    token_address: str = Field(description="Token address on source chain")
    amount: str = Field(description="Amount to bridge in human-readable format")
    bridge_fee: str = Field(description="Bridge fee in USD")
    estimated_time: str = Field(description="Estimated bridge time (e.g., '5-10 minutes')")
    bridge_protocol: str = Field(description="Bridge protocol used (e.g., 'LayerZero', 'Wormhole')")
    transaction_hash: Optional[str] = Field(
        default=None, description="Transaction hash if bridge is initiated"
    )
    status: str = Field(description="Bridge status: pending, completed, failed")


class BridgeOption(BaseModel):
    bridge_protocol: str = Field(description="Bridge protocol name")
    bridge_fee: str = Field(description="Bridge fee in USD")
    bridge_fee_usd: float = Field(description="Bridge fee as number for sorting")
    estimated_time: str = Field(description="Estimated bridge time")
    min_amount: Optional[str] = Field(default=None, description="Minimum bridge amount")
    max_amount: Optional[str] = Field(default=None, description="Maximum bridge amount")
    is_recommended: Optional[bool] = Field(
        default=False, description="Is this the recommended option (lowest fee)"
    )


class BridgeBalanceCheck(BaseModel):
    account_address: str = Field(description="Account address checked")
    token_symbol: str = Field(description="Token symbol")
    balance: str = Field(description="Current balance")
    balance_sufficient: bool = Field(description="Whether balance is sufficient")
    required_amount: str = Field(description="Amount required (including fees)")


class StructuredBridge(BaseModel):
    type: str = Field(default="bridge", description="Response type")
    source_chain: str = Field(description="Source chain")
    destination_chain: str = Field(description="Destination chain")
    token_symbol: str = Field(description="Token symbol")
    amount: str = Field(description="Amount to bridge")
    account_address: Optional[str] = Field(default=None, description="Account address")
    balance_check: Optional[BridgeBalanceCheck] = Field(
        default=None, description="Balance check result"
    )
    bridge_options: Optional[list[BridgeOption]] = Field(
        default=None, description="Available bridge options with fees"
    )
    transaction: Optional[BridgeTransaction] = Field(
        default=None, description="Bridge transaction details (if initiated)"
    )
    requires_confirmation: Optional[bool] = Field(
        default=False,
        description="Whether explicit confirmation is required due to high amount",
    )
    confirmation_threshold: Optional[float] = Field(
        default=None, description="The threshold amount that requires confirmation"
    )
    amount_exceeds_threshold: Optional[bool] = Field(
        default=False,
        description="Whether the amount exceeds the confirmation threshold",
    )
    error: Optional[str] = Field(default=None, description="Error message if any")


class BridgeAgent:
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
            name="bridge_agent",
            description="An agent that handles token bridging across blockchain chains including Polygon and Hedera",
            instruction="""
You are a blockchain bridge agent. Your role is to help users bridge tokens between different blockchain chains.

When you receive a bridge request, analyze:
- The source chain (hedera or polygon)
- The destination chain (hedera or polygon)
- The token to bridge (symbol and address)
- The amount to bridge

Return a structured JSON response with bridge transaction details.
            """,
            tools=[],
        )

    async def invoke(self, query: str, session_id: str) -> str:
        # HARDCODED RESPONSE FOR TESTING - ALWAYS RETURNS JSON, NEVER CALLS LLM
        # This method completely bypasses the LLM and returns hardcoded data
        # TODO: Replace with actual bridge implementation later

        # IMPORTANT: This method NEVER calls self._runner or self._agent.run_async()
        # It ALWAYS returns hardcoded JSON data, bypassing all LLM calls

        print(f"🌉 Bridge Agent received query: {query}")
        print("⚠️  Using HARDCODED response - LLM is NOT being called")
        print("🔒 Bypassing LLM completely - returning hardcoded JSON response")

        # Parse query to extract bridge parameters
        source_chain = "hedera"  # Default
        destination_chain = "polygon"  # Default
        token_symbol = "USDC"  # Default
        amount = "100.0"  # Default
        account_address = None

        if not query or not query.strip():
            query = "bridge 100 USDC from hedera to polygon"

        query_lower = query.lower()
        query_upper = query.upper()

        # Extract account address
        hedera_match = re.search(r"0\.0\.\d+", query)
        evm_match = re.search(r"0x[a-fA-F0-9]{40}", query)
        if hedera_match:
            account_address = hedera_match.group()
        elif evm_match:
            account_address = evm_match.group()

        # Extract source chain
        if "from hedera" in query_lower or "hedera to" in query_lower:
            source_chain = "hedera"
        elif "from polygon" in query_lower or "polygon to" in query_lower:
            source_chain = "polygon"

        # Extract destination chain
        if "to hedera" in query_lower or "hedera" in query_lower[-10:]:
            destination_chain = "hedera"
        elif "to polygon" in query_lower or "polygon" in query_lower[-10:]:
            destination_chain = "polygon"

        # Extract token symbol
        token_symbols = ["HBAR", "USDC", "USDT", "MATIC", "ETH", "WBTC", "DAI"]
        for token in token_symbols:
            if token.lower() in query_lower:
                token_symbol = token
                break

        # Extract amount
        amount_match = re.search(r"(\d+\.?\d*)\s*(?:USDC|USDT|HBAR|MATIC|ETH|WBTC|DAI)?", query)
        if amount_match:
            amount = amount_match.group(1)

        # Check for explicit parameters in query
        if "source:" in query_lower or "source=" in query_lower:
            if "hedera" in query_lower:
                source_chain = "hedera"
            elif "polygon" in query_lower:
                source_chain = "polygon"

        if "destination:" in query_lower or "dest:" in query_lower or "destination=" in query_lower:
            if "hedera" in query_lower:
                destination_chain = "hedera"
            elif "polygon" in query_lower:
                destination_chain = "polygon"

        if "token:" in query_lower or "token=" in query_lower:
            for token in token_symbols:
                if token.lower() in query_lower:
                    token_symbol = token
                    break

        if "amount:" in query_lower or "amount=" in query_lower:
            amount_match = re.search(r"amount[:\s=]+(\d+\.?\d*)", query_lower)
            if amount_match:
                amount = amount_match.group(1)

        if "account:" in query_lower or "address:" in query_lower:
            account_match = re.search(
                r"(?:account|address)[:\s=]+(0\.0\.\d+|0x[a-fA-F0-9]{40})", query
            )
            if account_match:
                account_address = account_match.group(1)

        print(
            f"📊 Parsed: source={source_chain}, destination={destination_chain}, token={token_symbol}, amount={amount}, account={account_address}"
        )

        # Hardcoded bridge response
        # Generate a mock transaction hash
        import random

        tx_hash = f"0x{''.join([random.choice('0123456789abcdef') for _ in range(64)])}"

        # Determine token address based on chain
        token_addresses = {
            "hedera": {
                "USDC": "0.0.123456",
                "USDT": "0.0.234567",
                "HBAR": "0.0.0",
            },
            "polygon": {
                "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
                "MATIC": "0x0000000000000000000000000000000000000000",
            },
        }

        token_address = token_addresses.get(source_chain, {}).get(
            token_symbol, "0x0000000000000000000000000000000000000000"
        )

        # Mock balance check (hardcoded for now)
        # In production, this would call the Balance Agent to get actual balance
        try:
            amount_float = float(amount)
        except Exception:
            amount_float = 100.0

        # Hardcoded balance (in production, fetch from Balance Agent)
        mock_balance = 5000.0  # Assume user has 5000 tokens
        balance_sufficient = mock_balance >= amount_float

        balance_check = None
        if account_address:
            balance_check = {
                "account_address": account_address,
                "token_symbol": token_symbol,
                "balance": f"{mock_balance:.2f}",
                "balance_sufficient": balance_sufficient,
                "required_amount": f"{amount_float:.2f}",
            }

        # Generate multiple bridge options with different fees
        # Simulate different bridge protocols with varying fees
        bridge_protocols = [
            {"name": "LayerZero", "fee_percent": 0.08, "time": "5-10 minutes"},
            {"name": "Wormhole", "fee_percent": 0.12, "time": "3-7 minutes"},
            {"name": "Stargate", "fee_percent": 0.10, "time": "4-8 minutes"},
            {"name": "Multichain", "fee_percent": 0.15, "time": "6-12 minutes"},
        ]

        bridge_options = []
        for protocol in bridge_protocols:
            fee_usd = amount_float * (protocol["fee_percent"] / 100)
            bridge_options.append(
                {
                    "bridge_protocol": protocol["name"],
                    "bridge_fee": f"${fee_usd:.2f}",
                    "bridge_fee_usd": fee_usd,
                    "estimated_time": protocol["time"],
                    "min_amount": "10.0",
                    "max_amount": "100000.0",
                    "is_recommended": False,
                }
            )

        # Sort by fee and mark the lowest as recommended
        bridge_options.sort(key=lambda x: x["bridge_fee_usd"])
        if bridge_options:
            bridge_options[0]["is_recommended"] = True

        # Define threshold for requiring confirmation (e.g., $100 or 100 tokens)
        # If amount exceeds this, require explicit confirmation
        CONFIRMATION_THRESHOLD = 100.0  # Adjust based on your needs

        # Check if amount requires confirmation
        requires_confirmation = amount_float > CONFIRMATION_THRESHOLD

        # Check if this is a bridge initiation request (contains "initiate" or "execute" or "confirm")
        initiate_bridge = False
        selected_protocol = None

        # Check for explicit confirmation phrases
        confirmation_phrases = [
            "okay bridge",
            "ok bridge",
            "confirm bridge",
            "bridge now",
            "proceed",
            "yes bridge",
            "go ahead",
            "execute bridge",
        ]
        has_confirmation = any(phrase in query_lower for phrase in confirmation_phrases)

        if "initiate" in query_lower or "execute" in query_lower or has_confirmation:
            # If amount is high, require explicit confirmation
            if requires_confirmation and not has_confirmation:
                # Don't initiate - will be handled by setting requires_confirmation flag
                pass
            else:
                initiate_bridge = True
                # Extract protocol name if mentioned
                for protocol in bridge_protocols:
                    if protocol["name"].lower() in query_lower:
                        selected_protocol = protocol["name"]
                        break
                # Default to recommended (lowest fee) if not specified
                if not selected_protocol and bridge_options:
                    selected_protocol = bridge_options[0]["bridge_protocol"]

        # Build response - return bridge options (not transaction yet)
        hardcoded_bridge = {
            "type": "bridge",
            "source_chain": source_chain,
            "destination_chain": destination_chain,
            "token_symbol": token_symbol,
            "amount": amount,
            "account_address": account_address,
            "balance_check": balance_check,
            "bridge_options": bridge_options,
            "transaction": None,  # Will be set when user clicks "Bridge" button
            "requires_confirmation": requires_confirmation,
            "confirmation_threshold": CONFIRMATION_THRESHOLD,
            "amount_exceeds_threshold": requires_confirmation,
        }

        # If initiating bridge, create transaction
        # Only proceed if amount is below threshold OR user has explicitly confirmed
        if (
            initiate_bridge
            and selected_protocol
            and (not requires_confirmation or has_confirmation)
        ):
            import random

            tx_hash = f"0x{''.join([random.choice('0123456789abcdef') for _ in range(64)])}"

            # Find the selected protocol's fee
            selected_option = next(
                (opt for opt in bridge_options if opt["bridge_protocol"] == selected_protocol),
                bridge_options[0],
            )

            transaction = {
                "source_chain": source_chain,
                "destination_chain": destination_chain,
                "token_symbol": token_symbol,
                "token_address": token_address,
                "amount": amount,
                "bridge_fee": selected_option["bridge_fee"],
                "estimated_time": selected_option["estimated_time"],
                "bridge_protocol": selected_protocol,
                "transaction_hash": tx_hash,
                "status": "pending",
            }
            hardcoded_bridge["transaction"] = transaction
            print(
                f"🌉 Initiating bridge with {selected_protocol}, fee: {selected_option['bridge_fee']}"
            )

        # Always return valid JSON - never call LLM
        try:
            validated_bridge = StructuredBridge(**hardcoded_bridge)
            final_response = json.dumps(validated_bridge.model_dump(), indent=2)
            print("✅ Returning hardcoded bridge response")
            print(f"📦 Response length: {len(final_response)} chars")
            print(f"📄 Response preview: {final_response[:200]}...")

            # Validate it's parseable JSON
            json.loads(final_response)  # Validate it's parseable

            return final_response
        except Exception as e:
            print(f"❌ Validation error: {e}")
            import traceback

            traceback.print_exc()
            # Return a valid error response in JSON format
            error_response = json.dumps(
                {
                    "type": "bridge",
                    "source_chain": source_chain,
                    "destination_chain": destination_chain,
                    "token_symbol": token_symbol,
                    "amount": amount,
                    "account_address": account_address,
                    "balance_check": balance_check,
                    "bridge_options": bridge_options if "bridge_options" in locals() else [],
                    "transaction": None,
                    "error": f"Validation failed: {str(e)}",
                },
                indent=2,
            )
            return error_response


class BridgeExecutor(AgentExecutor):
    def __init__(self):
        self.agent = BridgeAgent()

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
                        "type": "bridge",
                        "source_chain": "unknown",
                        "destination_chain": "unknown",
                        "token_symbol": "unknown",
                        "amount": "0",
                        "transaction": {
                            "source_chain": "unknown",
                            "destination_chain": "unknown",
                            "token_symbol": "unknown",
                            "token_address": "unknown",
                            "amount": "0",
                            "bridge_fee": "$0.00",
                            "estimated_time": "unknown",
                            "bridge_protocol": "unknown",
                            "transaction_hash": None,
                            "status": "failed",
                        },
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
                        "type": "bridge",
                        "source_chain": "unknown",
                        "destination_chain": "unknown",
                        "token_symbol": "unknown",
                        "amount": "0",
                        "transaction": {
                            "source_chain": "unknown",
                            "destination_chain": "unknown",
                            "token_symbol": "unknown",
                            "token_address": "unknown",
                            "amount": "0",
                            "bridge_fee": "$0.00",
                            "estimated_time": "unknown",
                            "bridge_protocol": "unknown",
                            "transaction_hash": None,
                            "status": "failed",
                        },
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
                    "type": "bridge",
                    "source_chain": "unknown",
                    "destination_chain": "unknown",
                    "token_symbol": "unknown",
                    "amount": "0",
                    "transaction": {
                        "source_chain": "unknown",
                        "destination_chain": "unknown",
                        "token_symbol": "unknown",
                        "token_address": "unknown",
                        "amount": "0",
                        "bridge_fee": "$0.00",
                        "estimated_time": "unknown",
                        "bridge_protocol": "unknown",
                        "transaction_hash": None,
                        "status": "failed",
                    },
                    "error": f"Execution error: {str(e)}",
                },
                indent=2,
            )
            await event_queue.enqueue_event(new_agent_text_message(error_response))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")
