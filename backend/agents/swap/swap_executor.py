"""
Swap Agent (ADK + A2A Protocol)

This agent handles token swaps on blockchain chains.
It exposes an A2A Protocol endpoint so it can be called by the orchestrator.
TEMPORARY: Direct swap without quotes - executes swap immediately.
"""

import os
import json
import re
import random
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


class SwapTransaction(BaseModel):
    chain: str = Field(description="Chain (hedera or polygon)")
    token_in_symbol: str = Field(
        description="Token symbol to swap from (e.g., HBAR, USDC)"
    )
    token_in_address: str = Field(description="Token address to swap from")
    token_out_symbol: str = Field(
        description="Token symbol to swap to (e.g., USDC, HBAR)"
    )
    token_out_address: str = Field(description="Token address to swap to")
    amount_in: str = Field(description="Amount to swap in human-readable format")
    amount_out: str = Field(description="Amount out in human-readable format")
    amount_out_min: str = Field(description="Minimum amount out")
    swap_fee: str = Field(description="Swap fee")
    swap_fee_percent: float = Field(description="Swap fee percentage")
    estimated_time: str = Field(description="Estimated swap time (e.g., '~30 seconds')")
    dex_name: str = Field(description="DEX name (e.g., SaucerSwap, HeliSwap)")
    pool_address: str = Field(description="Pool contract address")
    slippage_tolerance: float = Field(description="Slippage tolerance percentage")
    transaction_hash: Optional[str] = Field(
        default=None, description="Transaction hash if swap is initiated"
    )
    status: str = Field(description="Swap status: pending, completed, failed")
    price_impact: Optional[str] = Field(
        default=None, description="Price impact percentage"
    )


class SwapOption(BaseModel):
    dex_name: str = Field(description="DEX name")
    amount_out: str = Field(description="Estimated amount out")
    swap_fee: str = Field(description="Swap fee")
    swap_fee_percent: float = Field(description="Swap fee percentage")
    price_impact: Optional[str] = Field(default=None, description="Price impact")
    estimated_time: str = Field(description="Estimated swap time")
    pool_address: str = Field(description="Pool contract address")
    is_recommended: Optional[bool] = Field(
        default=False, description="Is this the recommended option (best rate)"
    )


class SwapBalanceCheck(BaseModel):
    account_address: str = Field(description="Account address checked")
    token_symbol: str = Field(description="Token symbol")
    balance: str = Field(description="Current balance")
    balance_sufficient: bool = Field(description="Whether balance is sufficient")
    required_amount: str = Field(description="Amount required (including fees)")


class StructuredSwap(BaseModel):
    type: str = Field(default="swap", description="Response type")
    chain: str = Field(description="Chain (hedera or polygon)")
    token_in_symbol: str = Field(description="Token symbol to swap from")
    token_out_symbol: str = Field(description="Token symbol to swap to")
    amount_in: str = Field(description="Amount to swap")
    account_address: Optional[str] = Field(default=None, description="Account address")
    balance_check: Optional[SwapBalanceCheck] = Field(
        default=None, description="Balance check result"
    )
    swap_options: Optional[list[SwapOption]] = Field(
        default=None,
        description="Available swap options (TEMPORARY: not used, direct swap)",
    )
    transaction: Optional[SwapTransaction] = Field(
        default=None, description="Swap transaction details (if initiated)"
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


class SwapAgent:
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
            name="swap_agent",
            description="An agent that handles token swaps on blockchain chains including Polygon and Hedera",
            instruction="""
You are a blockchain swap agent. Your role is to help users swap tokens on different blockchain chains.

When you receive a swap request, analyze:
- The chain (hedera or polygon)
- The token to swap from (symbol and address)
- The token to swap to (symbol and address)
- The amount to swap
- The slippage tolerance

TEMPORARY: Execute swap directly without getting quotes first.

Return a structured JSON response with swap transaction details.
            """,
            tools=[],
        )

    async def invoke(self, query: str, session_id: str) -> str:
        # TEMPORARY: Direct swap without quotes - executes swap immediately
        # This method completely bypasses the LLM and returns hardcoded swap transaction

        print(f"💱 Swap Agent received query: {query}")
        print("⚠️  Using DIRECT SWAP (no quotes) - LLM is NOT being called")
        print("🔒 Bypassing LLM completely - returning direct swap transaction")

        # Parse query to extract swap parameters
        chain = "hedera"  # Default
        token_in_symbol = "HBAR"  # Default
        token_out_symbol = "USDC"  # Default
        amount_in = "0.01"  # Default (small amount for testing)
        account_address = None
        slippage_tolerance = 0.5  # Default 0.5%

        if not query or not query.strip():
            query = "Swap 0.01 HBAR to USDC on hedera"

        query_lower = query.lower()

        # Extract account address
        hedera_match = re.search(r"0\.0\.\d+", query)
        evm_match = re.search(r"0x[a-fA-F0-9]{40}", query)
        if hedera_match:
            account_address = hedera_match.group()
        elif evm_match:
            account_address = evm_match.group()

        # Extract chain
        if "hedera" in query_lower:
            chain = "hedera"
        elif "polygon" in query_lower:
            chain = "polygon"

        # Extract token symbols
        token_symbols = ["HBAR", "USDC", "USDT", "MATIC", "ETH", "WBTC", "DAI"]
        found_tokens = []
        for token in token_symbols:
            if token.lower() in query_lower:
                found_tokens.append(token)

        if len(found_tokens) >= 2:
            token_in_symbol = found_tokens[0]
            token_out_symbol = found_tokens[1]
        elif len(found_tokens) == 1:
            token_in_symbol = found_tokens[0]
            # Default output token
            if token_in_symbol == "HBAR":
                token_out_symbol = "USDC"
            else:
                token_out_symbol = "HBAR"

        # Extract amount
        amount_match = re.search(r"(\d+\.?\d*)", query)
        if amount_match:
            amount_in = amount_match.group(1)

        # Extract slippage
        slippage_match = re.search(r"slippage[:\s=]+(\d+\.?\d*)", query_lower)
        if slippage_match:
            slippage_tolerance = float(slippage_match.group(1))

        # Check for explicit parameters
        if "chain:" in query_lower or "chain=" in query_lower:
            if "hedera" in query_lower:
                chain = "hedera"
            elif "polygon" in query_lower:
                chain = "polygon"

        if "account:" in query_lower or "address:" in query_lower:
            account_match = re.search(
                r"(?:account|address)[:\s=]+(0\.0\.\d+|0x[a-fA-F0-9]{40})", query
            )
            if account_match:
                account_address = account_match.group(1)

        print(
            f"📊 Parsed: chain={chain}, tokenIn={token_in_symbol}, tokenOut={token_out_symbol}, amount={amount_in}, account={account_address}, slippage={slippage_tolerance}%"
        )

        # Determine token addresses based on chain
        token_addresses = {
            "hedera": {
                "HBAR": "0.0.0",
                "USDC": "0.0.456858",
                "USDT": "0.0.1055472",
            },
            "polygon": {
                "MATIC": "0x0000000000000000000000000000000000000000",
                "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
                "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
            },
        }

        token_in_address = token_addresses.get(chain, {}).get(
            token_in_symbol, "0x0000000000000000000000000000000000000000"
        )
        token_out_address = token_addresses.get(chain, {}).get(
            token_out_symbol, "0x0000000000000000000000000000000000000000"
        )

        # Mock balance check
        try:
            amount_float = float(amount_in)
        except Exception:
            amount_float = 0.01

        # Hardcoded balance (in production, fetch from Balance Agent)
        mock_balance = 1000.0  # Assume user has 1000 tokens
        balance_sufficient = mock_balance >= amount_float

        balance_check = None
        if account_address:
            balance_check = {
                "account_address": account_address,
                "token_symbol": token_in_symbol,
                "balance": f"{mock_balance:.2f}",
                "balance_sufficient": balance_sufficient,
                "required_amount": f"{amount_float:.2f}",
            }

        # TEMPORARY: Direct swap - calculate estimated output (simple 1:1 for now)
        # In production, this would query DEX pools for actual rates
        amount_out_float = amount_float * 0.995  # Assume 0.5% fee
        amount_out = f"{amount_out_float:.6f}"
        amount_out_min_float = amount_out_float * (1 - slippage_tolerance / 100)
        amount_out_min = f"{amount_out_min_float:.6f}"

        # Default DEX based on chain
        if chain == "hedera":
            dex_name = "SaucerSwap"
            pool_address = (
                "0x0000000000000000000000000000000000163B5a"  # WHBAR/USDC pool
            )
        else:
            dex_name = "QuickSwap"
            pool_address = "0x1234567890ABCDEF1234567890ABCDEF12345678"

        # Generate transaction hash
        tx_hash = f"0x{''.join([random.choice('0123456789abcdef') for _ in range(64)])}"

        # TEMPORARY: Direct swap - create transaction immediately (no quotes)
        # Check if this is an initiation request
        confirmation_phrases = [
            "okay swap",
            "ok swap",
            "confirm swap",
            "swap now",
            "proceed",
            "yes swap",
            "go ahead",
            "execute swap",
            "initiate swap",
        ]
        has_confirmation = any(phrase in query_lower for phrase in confirmation_phrases)

        # If query contains "initiate" or confirmation phrases, proceed with swap
        if (
            "initiate" in query_lower or has_confirmation or True
        ):  # Always true for direct swap
            transaction = {
                "chain": chain,
                "token_in_symbol": token_in_symbol,
                "token_in_address": token_in_address,
                "token_out_symbol": token_out_symbol,
                "token_out_address": token_out_address,
                "amount_in": amount_in,
                "amount_out": amount_out,
                "amount_out_min": amount_out_min,
                "swap_fee": f"${amount_float * 0.003:.2f}",  # 0.3% fee
                "swap_fee_percent": 0.3,
                "estimated_time": "~30 seconds",
                "dex_name": dex_name,
                "pool_address": pool_address,
                "slippage_tolerance": slippage_tolerance,
                "transaction_hash": tx_hash,
                "status": "pending",
                "price_impact": "0.1%",
            }
            print(
                f"💱 Direct swap transaction created: {amount_in} {token_in_symbol} -> {amount_out} {token_out_symbol}"
            )
        else:
            transaction = None

        # Build response - TEMPORARY: Direct swap, no options
        hardcoded_swap = {
            "type": "swap",
            "chain": chain,
            "token_in_symbol": token_in_symbol,
            "token_out_symbol": token_out_symbol,
            "amount_in": amount_in,
            "account_address": account_address,
            "balance_check": balance_check,
            "swap_options": None,  # No options for direct swap
            "transaction": transaction,  # Direct swap transaction
            "requires_confirmation": False,  # No confirmation needed for small amounts
            "confirmation_threshold": 100.0,
            "amount_exceeds_threshold": False,
        }

        # Always return valid JSON - never call LLM
        try:
            validated_swap = StructuredSwap(**hardcoded_swap)
            final_response = json.dumps(validated_swap.model_dump(), indent=2)
            print("✅ Returning direct swap transaction response")
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
                    "type": "swap",
                    "chain": chain,
                    "token_in_symbol": token_in_symbol,
                    "token_out_symbol": token_out_symbol,
                    "amount_in": amount_in,
                    "account_address": account_address,
                    "balance_check": balance_check,
                    "swap_options": None,
                    "transaction": None,
                    "error": f"Validation failed: {str(e)}",
                },
                indent=2,
            )
            return error_response


class SwapExecutor(AgentExecutor):
    def __init__(self):
        self.agent = SwapAgent()

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
                        "type": "swap",
                        "chain": "unknown",
                        "token_in_symbol": "unknown",
                        "token_out_symbol": "unknown",
                        "amount_in": "0",
                        "transaction": {
                            "chain": "unknown",
                            "token_in_symbol": "unknown",
                            "token_in_address": "unknown",
                            "token_out_symbol": "unknown",
                            "token_out_address": "unknown",
                            "amount_in": "0",
                            "amount_out": "0",
                            "amount_out_min": "0",
                            "swap_fee": "$0.00",
                            "swap_fee_percent": 0.0,
                            "estimated_time": "unknown",
                            "dex_name": "unknown",
                            "pool_address": "unknown",
                            "slippage_tolerance": 0.5,
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
                        "type": "swap",
                        "chain": "unknown",
                        "token_in_symbol": "unknown",
                        "token_out_symbol": "unknown",
                        "amount_in": "0",
                        "transaction": {
                            "chain": "unknown",
                            "token_in_symbol": "unknown",
                            "token_in_address": "unknown",
                            "token_out_symbol": "unknown",
                            "token_out_address": "unknown",
                            "amount_in": "0",
                            "amount_out": "0",
                            "amount_out_min": "0",
                            "swap_fee": "$0.00",
                            "swap_fee_percent": 0.0,
                            "estimated_time": "unknown",
                            "dex_name": "unknown",
                            "pool_address": "unknown",
                            "slippage_tolerance": 0.5,
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
                    "type": "swap",
                    "chain": "unknown",
                    "token_in_symbol": "unknown",
                    "token_out_symbol": "unknown",
                    "amount_in": "0",
                    "transaction": {
                        "chain": "unknown",
                        "token_in_symbol": "unknown",
                        "token_in_address": "unknown",
                        "token_out_symbol": "unknown",
                        "token_out_address": "unknown",
                        "amount_in": "0",
                        "amount_out": "0",
                        "amount_out_min": "0",
                        "swap_fee": "$0.00",
                        "swap_fee_percent": 0.0,
                        "estimated_time": "unknown",
                        "dex_name": "unknown",
                        "pool_address": "unknown",
                        "slippage_tolerance": 0.5,
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
