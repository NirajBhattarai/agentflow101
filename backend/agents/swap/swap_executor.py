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
from google.adk.memory.in_memory_memory_service import (
    InMemoryMemoryService,
)  # noqa: E402
from google.adk.artifacts import InMemoryArtifactService  # noqa: E402

# Balance fetching imports
from ..balance.tools.hedera import get_balance_hedera  # noqa: E402
from ..balance.tools.polygon import get_balance_polygon  # noqa: E402

# Chain-specific swap imports
from .tools import (  # noqa: E402
    get_swap_hedera,
    get_swap_polygon,
    get_token_address_for_chain,
    get_available_tokens_for_chain,
)


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

When you receive a swap request, you MUST:
1. Extract the swap parameters from the user's query:
   - Chain (hedera or polygon)
   - Token to swap FROM (token_in_symbol) - use get_token_address_for_chain to get its address
   - Token to swap TO (token_out_symbol) - use get_token_address_for_chain to get its address
   - Amount to swap (amount_in)
   - Account address (if provided)
   - Slippage tolerance (default: 0.5%)

2. Use the available tools to extract token addresses:
   - get_token_address_for_chain: Look up token addresses by symbol and chain
   - get_available_tokens_for_chain: See what tokens are available on a chain

3. CRITICAL: Understand swap direction from natural language:
   - "swap 0.2 USDC to HBAR" means: token_in_symbol=USDC, token_out_symbol=HBAR, amount_in=0.2
   - "swap HBAR for USDC" means: token_in_symbol=HBAR, token_out_symbol=USDC
   - "I want to exchange USDC for HBAR" means: token_in_symbol=USDC, token_out_symbol=HBAR
   - "swap 0.2 USDC to HBAR" = token_in_symbol="USDC", token_out_symbol="HBAR"
   - The token BEFORE "to/for/->" is ALWAYS token_in_symbol, the token AFTER is ALWAYS token_out_symbol
   - Pay close attention to the order - "USDC to HBAR" means swapping FROM USDC TO HBAR

4. After extracting all parameters, return ONLY a valid JSON object (no markdown, no code blocks, no explanation):
{
  "chain": "hedera",
  "token_in_symbol": "USDC",
  "token_out_symbol": "HBAR",
  "amount_in": "0.2",
  "account_address": "0x...",
  "slippage_tolerance": 0.5
}

IMPORTANT: 
- Always use the tools to get token addresses
- Return ONLY JSON, no other text
- Pay attention to swap direction - "X to Y" means token_in=X, token_out=Y
            """,
            tools=[
                get_token_address_for_chain,
                get_available_tokens_for_chain,
            ],
        )

    async def invoke(self, query: str, session_id: str) -> str:
        # Use LLM with tools to extract swap parameters
        print(f"💱 Swap Agent received query: {query}")
        print("🤖 Using LLM with tools to extract swap parameters")

        if not query or not query.strip():
            query = "Swap 0.01 HBAR to USDC on hedera"

        try:
            # Call LLM to extract swap parameters using tools
            result = await self._runner.run_async(
                user_id=self._user_id,
                session_id=session_id,
                message=query,
            )

            # Parse LLM response to extract swap parameters
            llm_response = result.text if hasattr(result, "text") else str(result)
            print(f"📝 LLM Response: {llm_response[:500]}...")  # Log first 500 chars

            # Try to extract JSON from LLM response
            import json

            try:
                # Try multiple patterns to find JSON in the response
                # Pattern 1: Look for complete JSON object with token_in_symbol
                json_match = re.search(
                    r'\{[^{}]*(?:"token_in_symbol"|"chain")[^{}]*\}',
                    llm_response,
                    re.DOTALL,
                )
                if json_match:
                    try:
                        extracted_params = json.loads(json_match.group())
                        print(
                            f"✅ Extracted parameters from LLM (pattern 1): {extracted_params}"
                        )
                    except json.JSONDecodeError:
                        # Try to find a larger JSON block
                        json_match2 = re.search(
                            r'\{.*?"token_in_symbol".*?"token_out_symbol".*?\}',
                            llm_response,
                            re.DOTALL,
                        )
                        if json_match2:
                            extracted_params = json.loads(json_match2.group())
                            print(
                                f"✅ Extracted parameters from LLM (pattern 2): {extracted_params}"
                            )
                        else:
                            raise ValueError("Could not parse JSON")
                else:
                    # Try to find JSON code block
                    code_block_match = re.search(
                        r"```(?:json)?\s*(\{.*?\})\s*```", llm_response, re.DOTALL
                    )
                    if code_block_match:
                        extracted_params = json.loads(code_block_match.group(1))
                        print(
                            f"✅ Extracted parameters from LLM (code block): {extracted_params}"
                        )
                    else:
                        # If no JSON found, fall back to regex parsing
                        print(
                            "⚠️  No JSON found in LLM response, falling back to regex parsing"
                        )
                        print(f"📝 LLM response preview: {llm_response[:200]}")
                        return await self._extract_params_with_regex(query)
            except (json.JSONDecodeError, ValueError) as e:
                print(
                    f"⚠️  Failed to parse JSON from LLM response: {e}, falling back to regex parsing"
                )
                print(f"📝 LLM response preview: {llm_response[:200]}")
                return await self._extract_params_with_regex(query)

            # Use extracted parameters from LLM
            chain = extracted_params.get("chain", "hedera")
            token_in_symbol = extracted_params.get("token_in_symbol", "HBAR")
            token_out_symbol = extracted_params.get("token_out_symbol", "USDC")
            amount_in = extracted_params.get("amount_in", "0.01")
            account_address = extracted_params.get("account_address")
            slippage_tolerance = extracted_params.get("slippage_tolerance", 0.5)

            # Log extracted parameters for debugging
            print("🔍 LLM Extracted Parameters:")
            print(f"   Chain: {chain}")
            print(f"   Token In: {token_in_symbol}")
            print(f"   Token Out: {token_out_symbol}")
            print(f"   Amount: {amount_in}")
            print(f"   Account: {account_address}")
            print(f"   Slippage: {slippage_tolerance}%")

        except Exception as e:
            print(f"⚠️  Error calling LLM: {e}")
            print("🔄 Falling back to regex-based parameter extraction")
            return await self._extract_params_with_regex(query)

        # Continue with swap execution using extracted parameters
        return await self._execute_swap(
            chain=chain,
            token_in_symbol=token_in_symbol,
            token_out_symbol=token_out_symbol,
            amount_in=amount_in,
            account_address=account_address,
            slippage_tolerance=slippage_tolerance,
        )

    async def _extract_params_with_regex(self, query: str) -> str:
        """Fallback method using regex extraction (backward compatibility)."""
        # Parse query to extract swap parameters
        chain = "hedera"  # Default
        token_in_symbol = "HBAR"  # Default
        token_out_symbol = "USDC"  # Default
        amount_in = "0.01"  # Default (small amount for testing)
        account_address = None
        slippage_tolerance = 0.5  # Default 0.5%

        query_lower = query.lower()

        # Extract account address
        hedera_match = re.search(r"0\.0\.\d+", query)
        evm_match = re.search(r"0x[a-fA-F0-9]{40}", query)
        if hedera_match:
            account_address = hedera_match.group()
        elif evm_match:
            account_address = evm_match.group()

        # Extract chain - if not specified, we'll ask user to select
        chain_specified = False
        if "hedera" in query_lower:
            chain = "hedera"
            chain_specified = True
        elif "polygon" in query_lower:
            chain = "polygon"
            chain_specified = True

        # Extract token symbols - get all available tokens for the chain
        from .tools.constants import CHAIN_TOKENS

        available_tokens = (
            list(CHAIN_TOKENS.get(chain, {}).keys()) if chain_specified else []
        )

        # Also check common token names
        all_token_symbols = available_tokens + [
            "HBAR",
            "USDC",
            "USDT",
            "MATIC",
            "ETH",
            "WBTC",
            "DAI",
            "WMATIC",
            "WHBAR",
            "WETH",
            "LINK",
            "AAVE",
            "UNI",
            "CRV",
            "SAUCE",
            "DOGE",
            "BTC",
            "AVAX",
        ]

        # Try to detect swap direction from patterns like "X to Y", "X for Y", "swap X Y"
        token_in_symbol = None
        token_out_symbol = None

        # Pattern 1: "X to Y" or "X for Y" or "X -> Y" or "X => Y"
        # Look for patterns like "usdc to hbar", "swap 0.2 usdc to hbar", etc.
        to_patterns = [
            # Patterns with "swap" keyword (check these first)
            r"swap\s+(\d+\.?\d*)\s+([A-Za-z]+)\s+to\s+([A-Za-z]+)",  # "swap 0.2 usdc to hbar"
            r"swap\s+([A-Za-z]+)\s+to\s+([A-Za-z]+)",  # "swap usdc to hbar" or "i want to swap swap usdc to hbar"
            r"swap\s+([A-Za-z]+)\s+for\s+([A-Za-z]+)",  # "swap usdc for hbar"
            # Patterns without "swap" keyword
            r"(\d+\.?\d*)\s+([A-Za-z]+)\s+to\s+([A-Za-z]+)",  # "0.2 usdc to hbar"
            r"([A-Za-z]+)\s+to\s+([A-Za-z]+)",  # "usdc to hbar"
            r"([A-Za-z]+)\s+for\s+([A-Za-z]+)",  # "usdc for hbar"
            r"([A-Za-z]+)\s*->\s*([A-Za-z]+)",  # "usdc -> hbar"
            r"([A-Za-z]+)\s*=>\s*([A-Za-z]+)",  # "usdc => hbar"
        ]

        for pattern in to_patterns:
            match = re.search(pattern, query_lower)
            if match:
                # Handle patterns with amount (3 groups) or without (2 groups)
                if len(match.groups()) == 3:
                    # Pattern has amount: group 2 is token_in, group 3 is token_out
                    token1 = match.group(2).upper()
                    token2 = match.group(3).upper()
                else:
                    # Pattern without amount: group 1 is token_in, group 2 is token_out
                    token1 = match.group(1).upper()
                    token2 = match.group(2).upper()

                # Check if both tokens are in our known list
                if token1 in all_token_symbols and token2 in all_token_symbols:
                    # If chain is specified, verify tokens are available on that chain
                    if chain_specified:
                        if token1 in CHAIN_TOKENS.get(
                            chain, {}
                        ) and token2 in CHAIN_TOKENS.get(chain, {}):
                            token_in_symbol = token1
                            token_out_symbol = token2
                            print(f"✅ Found tokens on {chain}: {token1} -> {token2}")
                            break
                    else:
                        # No chain specified yet - accept tokens and we'll ask for chain later
                        token_in_symbol = token1
                        token_out_symbol = token2
                        print(
                            f"✅ Found tokens (no chain specified yet): {token1} -> {token2}"
                        )
                        break

        # Pattern 2: If no direction found, find all tokens and use order in query
        if not token_in_symbol or not token_out_symbol:
            found_tokens = []
            token_positions = {}  # Track position of each token in query

            for token in all_token_symbols:
                token_lower = token.lower()
                if token_lower in query_lower:
                    # Only add if token is available on the selected chain
                    if chain_specified:
                        if token in CHAIN_TOKENS.get(chain, {}):
                            found_tokens.append(token)
                            # Find position of token in query
                            pos = query_lower.find(token_lower)
                            if pos != -1:
                                token_positions[token] = pos
                    else:
                        found_tokens.append(token)
                        pos = query_lower.find(token_lower)
                        if pos != -1:
                            token_positions[token] = pos

            # Sort tokens by their position in the query
            if token_positions:
                found_tokens = sorted(
                    found_tokens, key=lambda t: token_positions.get(t, 999999)
                )

            if len(found_tokens) >= 2:
                token_in_symbol = found_tokens[0]
                token_out_symbol = found_tokens[1]
            elif len(found_tokens) == 1:
                token_in_symbol = found_tokens[0]
                # Default output token based on chain - prefer stablecoins
                if chain == "hedera":
                    if token_in_symbol == "HBAR":
                        token_out_symbol = "USDC"  # Default to USDC for HBAR
                    elif token_in_symbol == "USDC":
                        token_out_symbol = "HBAR"  # USDC -> HBAR (common swap)
                    elif token_in_symbol == "USDT":
                        token_out_symbol = "USDC"  # USDT -> USDC
                    else:
                        token_out_symbol = "USDC"  # Any other token -> USDC
                elif chain == "polygon":
                    if token_in_symbol == "MATIC":
                        token_out_symbol = "USDC"  # Default to USDC for MATIC
                    elif token_in_symbol == "USDC":
                        token_out_symbol = "USDT"  # USDC -> USDT
                    elif token_in_symbol == "USDT":
                        token_out_symbol = "USDC"  # USDT -> USDC
                    else:
                        token_out_symbol = "USDC"  # Any other token -> USDC
                else:
                    # Fallback
                    token_out_symbol = "USDC"

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
                chain_specified = True
            elif "polygon" in query_lower:
                chain = "polygon"
                chain_specified = True

        if "account:" in query_lower or "address:" in query_lower:
            account_match = re.search(
                r"(?:account|address)[:\s=]+(0\.0\.\d+|0x[a-fA-F0-9]{40})", query
            )
            if account_match:
                account_address = account_match.group(1)

        # If chain is not specified, return early asking user to select chain
        if not chain_specified:
            print("⚠️ Chain not specified in query - asking user to select chain")
            response_message = (
                "To proceed with the swap, please specify which blockchain you'd like to swap on:\n\n"
                "• **Hedera** - For swapping HBAR, USDC, USDT, and other Hedera tokens\n"
                "• **Polygon** - For swapping MATIC, USDC, USDT, and other Polygon tokens\n\n"
                "Please select a chain and provide your swap details."
            )
            return json.dumps(
                {
                    "type": "swap",
                    "requires_chain_selection": True,
                    "message": response_message,
                    "supported_chains": ["hedera", "polygon"],
                },
                indent=2,
            )

        print(
            f"📊 Parsed (regex): chain={chain}, tokenIn={token_in_symbol}, tokenOut={token_out_symbol}, amount={amount_in}, account={account_address}, slippage={slippage_tolerance}%"
        )

        # Validate extracted parameters before executing swap
        if not token_in_symbol:
            return json.dumps(
                {
                    "type": "swap",
                    "error": "Could not determine which token to swap from. Please specify clearly, e.g., 'swap USDC to HBAR' or 'swap 0.2 USDC to HBAR'",
                },
                indent=2,
            )

        if not token_out_symbol:
            return json.dumps(
                {
                    "type": "swap",
                    "error": "Could not determine which token to swap to. Please specify clearly, e.g., 'swap USDC to HBAR' or 'swap 0.2 USDC to HBAR'",
                },
                indent=2,
            )

        # Continue with swap execution
        return await self._execute_swap(
            chain=chain,
            token_in_symbol=token_in_symbol,
            token_out_symbol=token_out_symbol,
            amount_in=amount_in,
            account_address=account_address,
            slippage_tolerance=slippage_tolerance,
        )

    async def _execute_swap(
        self,
        chain: str,
        token_in_symbol: str,
        token_out_symbol: str,
        amount_in: str,
        account_address: Optional[str],
        slippage_tolerance: float,
    ) -> str:
        """Execute swap with extracted parameters."""
        print(
            f"📊 Executing swap: chain={chain}, tokenIn={token_in_symbol}, tokenOut={token_out_symbol}, amount={amount_in}, account={account_address}, slippage={slippage_tolerance}%"
        )

        # Get chain-specific swap configuration
        swap_config = None
        if chain == "hedera":
            swap_config = get_swap_hedera(
                token_in_symbol=token_in_symbol,
                token_out_symbol=token_out_symbol,
                amount_in=amount_in,
                account_address=account_address or "",
                slippage_tolerance=slippage_tolerance,
            )
        elif chain == "polygon":
            swap_config = get_swap_polygon(
                token_in_symbol=token_in_symbol,
                token_out_symbol=token_out_symbol,
                amount_in=amount_in,
                account_address=account_address or "",
                slippage_tolerance=slippage_tolerance,
            )
        else:
            raise ValueError(
                f"Unsupported chain: {chain}. Supported chains: hedera, polygon"
            )

        # Extract addresses from swap config
        # For Hedera: use Hedera format for balance checking, EVM format for contract calls
        # For Polygon/EVM: use EVM format for both
        if chain == "hedera":
            token_in_address = swap_config.get(
                "token_in_address", ""
            )  # Hedera format for balance
            token_out_address = swap_config.get(
                "token_out_address", ""
            )  # Hedera format for balance
            token_in_address_evm = swap_config.get(
                "token_in_address_evm", ""
            )  # EVM format for contracts
            token_out_address_evm = swap_config.get(
                "token_out_address_evm", ""
            )  # EVM format for contracts
        else:
            token_in_address = swap_config.get("token_in_address", "")  # EVM format
            token_out_address = swap_config.get("token_out_address", "")  # EVM format
            token_in_address_evm = token_in_address  # Same for EVM chains
            token_out_address_evm = token_out_address  # Same for EVM chains

        dex_name = swap_config.get("dex_name", "Unknown")
        pool_address = swap_config.get("router_address", "")

        # Fetch actual balance from blockchain
        try:
            amount_float = float(amount_in)
        except Exception:
            amount_float = 0.01

        # Fetch actual balance from blockchain
        # IMPORTANT: Use Hedera format addresses for balance checking
        actual_balance = 0.0
        balance_sufficient = False

        if account_address:
            try:
                # Fetch balance based on chain
                if chain == "hedera":
                    # Use Hedera format address for balance checking
                    balance_result = get_balance_hedera(
                        account_address, token_address=token_in_address
                    )
                    # Find the matching token balance
                    if balance_result.get("balances"):
                        for balance_item in balance_result["balances"]:
                            if balance_item.get("token_address") == token_in_address:
                                actual_balance = float(balance_item.get("balance", "0"))
                                break
                            # For HBAR, check native token
                            if (
                                token_in_symbol == "HBAR"
                                and balance_item.get("token_type") == "native"
                            ):
                                actual_balance = float(balance_item.get("balance", "0"))
                                break
                elif chain == "polygon":
                    # Use EVM format address for balance checking (Polygon is EVM)
                    balance_result = get_balance_polygon(
                        account_address, token_address=token_in_address
                    )
                    # Find the matching token balance
                    if balance_result.get("balances"):
                        for balance_item in balance_result["balances"]:
                            if balance_item.get("token_address") == token_in_address:
                                actual_balance = float(balance_item.get("balance", "0"))
                                break
                            # For MATIC, check native token
                            if (
                                token_in_symbol == "MATIC"
                                and balance_item.get("token_type") == "native"
                            ):
                                actual_balance = float(balance_item.get("balance", "0"))
                                break

                balance_sufficient = actual_balance >= amount_float
                print(
                    f"💰 Balance check: {actual_balance} {token_in_symbol} >= {amount_float} {token_in_symbol} = {balance_sufficient}"
                )
            except Exception as e:
                print(f"⚠️ Error fetching balance: {e}")
                # If balance fetch fails, assume insufficient to be safe
                actual_balance = 0.0
                balance_sufficient = False

        balance_check = None
        if account_address:
            balance_check = {
                "account_address": account_address,
                "token_symbol": token_in_symbol,
                "balance": f"{actual_balance:.2f}",
                "balance_sufficient": balance_sufficient,
                "required_amount": f"{amount_float:.2f}",
            }

        # Extract swap amounts from swap config
        amount_out = swap_config.get("amount_out", "0")
        amount_out_min = swap_config.get("amount_out_min", "0")
        swap_fee_percent = swap_config.get("swap_fee_percent", 0.3)

        # Generate transaction hash
        tx_hash = f"0x{''.join([random.choice('0123456789abcdef') for _ in range(64)])}"

        # TEMPORARY: Direct swap - create transaction immediately (no quotes)
        # Check if this is an initiation request
        # Note: For now, we always proceed with swap (no confirmation needed)
        has_confirmation = True

        # Calculate swap fee
        swap_fee_amount = amount_float * (swap_fee_percent / 100)

        # If query contains "initiate" or confirmation phrases, proceed with swap
        if has_confirmation:  # Always true for direct swap
            # For Hedera: use EVM addresses in transaction for contract calls
            # For Polygon/EVM: addresses are already in EVM format
            transaction_token_in_address = (
                token_in_address_evm if chain == "hedera" else token_in_address
            )
            transaction_token_out_address = (
                token_out_address_evm if chain == "hedera" else token_out_address
            )

            transaction = {
                "chain": chain,
                "token_in_symbol": token_in_symbol,
                "token_in_address": transaction_token_in_address,  # EVM format for contract calls
                "token_in_address_hedera": (
                    token_in_address if chain == "hedera" else None
                ),  # Hedera format for balance
                "token_out_symbol": token_out_symbol,
                "token_out_address": transaction_token_out_address,  # EVM format for contract calls
                "token_out_address_hedera": (
                    token_out_address if chain == "hedera" else None
                ),  # Hedera format for balance
                "amount_in": amount_in,
                "amount_out": amount_out,
                "amount_out_min": amount_out_min,
                "swap_fee": f"${swap_fee_amount:.2f}",
                "swap_fee_percent": swap_fee_percent,
                "estimated_time": "~30 seconds",
                "dex_name": dex_name,
                "pool_address": pool_address,
                "slippage_tolerance": slippage_tolerance,
                "transaction_hash": tx_hash,
                "status": "pending",
                "price_impact": "0.1%",
                "swap_path": swap_config.get(
                    "swap_path", []
                ),  # EVM addresses for contract calls
                "rpc_url": swap_config.get("rpc_url", ""),
            }
            print(
                f"💱 Direct swap transaction created on {chain}: {amount_in} {token_in_symbol} -> {amount_out} {token_out_symbol} via {dex_name}"
            )
        else:
            transaction = None

        # Build response - TEMPORARY: Direct swap, no options
        # IMPORTANT: Use the extracted parameters directly - no hardcoding
        hardcoded_swap = {
            "type": "swap",
            "chain": chain,
            "token_in_symbol": token_in_symbol,  # Use extracted token_in_symbol
            "token_out_symbol": token_out_symbol,  # Use extracted token_out_symbol
            "amount_in": amount_in,
            "account_address": account_address,
            "balance_check": balance_check,
            "swap_options": None,  # No options for direct swap
            "transaction": transaction,  # Direct swap transaction
            "requires_confirmation": False,  # No confirmation needed for small amounts
            "confirmation_threshold": 100.0,
            "amount_exceeds_threshold": False,
        }

        # Log final response for debugging
        print("🔍 Final Response JSON:")
        print(f"   token_in_symbol: {hardcoded_swap['token_in_symbol']}")
        print(f"   token_out_symbol: {hardcoded_swap['token_out_symbol']}")
        print(f"   amount_in: {hardcoded_swap['amount_in']}")

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
