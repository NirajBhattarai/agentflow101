"""
Swap Agent Definition

Defines the SwapAgent class that handles token swap queries.
"""

import json
import re
from google.adk.agents.llm_agent import LlmAgent  # noqa: E402
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.adk.memory.in_memory_memory_service import (
    InMemoryMemoryService,
)  # noqa: E402
from google.adk.artifacts import InMemoryArtifactService  # noqa: E402

from .tools import (  # noqa: E402
    get_token_address_for_chain,
    get_available_tokens_for_chain,
)
from .core.constants import (  # noqa: E402
    get_model_name,
    check_api_keys,
    DEFAULT_USER_ID,
    AGENT_NAME,
    AGENT_DESCRIPTION,
)
from .core.agent_instruction import AGENT_INSTRUCTION  # noqa: E402
from .services.query_parser import parse_swap_query  # noqa: E402
from .services.swap_executor_service import execute_swap  # noqa: E402
from .services.response_builder import (  # noqa: E402
    build_chain_selection_response,
    build_error_response,
    build_swap_response,
)
from .core.response_validator import validate_and_serialize_response  # noqa: E402


def _get_agent_tools() -> list:
    """Get list of tools for the agent."""
    return [
        get_token_address_for_chain,
        get_available_tokens_for_chain,
    ]


class SwapAgent:
    """Agent that handles token swaps on blockchain chains."""

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
            tools=_get_agent_tools(),
        )

    async def invoke(self, query: str, session_id: str) -> str:
        """Invoke the agent with a query."""
        print(f"💱 Swap Agent received query: {query}")
        if not query or not query.strip():
            query = "Swap 0.01 HBAR to USDC on hedera"
        try:
            params = await self._extract_params_with_llm(query, session_id)
            if params.get("requires_chain_selection"):
                return build_chain_selection_response()
            if params.get("error"):
                return build_error_response(
                    params["error"],
                    params.get("chain"),
                    params.get("token_in"),
                    params.get("token_out"),
                )
            swap_data = execute_swap(
                chain=params["chain"],
                token_in_symbol=params["token_in_symbol"],
                token_out_symbol=params["token_out_symbol"],
                amount_in=params["amount_in"],
                account_address=params.get("account_address"),
                slippage_tolerance=params.get("slippage_tolerance", 0.5),
            )
            response_data = build_swap_response(swap_data)
            return validate_and_serialize_response(response_data)
        except Exception as e:
            print(f"❌ Error in invoke: {e}")
            parsed = parse_swap_query(query)
            return build_error_response("execution_error", parsed.get("chain"))

    async def _extract_params_with_llm(self, query: str, session_id: str) -> dict:
        """Extract swap parameters using LLM."""
        try:
            result = await self._runner.run_async(
                user_id=self._user_id,
                session_id=session_id,
                message=query,
            )
            llm_response = result.text if hasattr(result, "text") else str(result)
            print(f"📝 LLM Response: {llm_response[:500]}...")
            return self._parse_llm_response(llm_response, query)
        except Exception as e:
            print(f"⚠️  Error calling LLM: {e}")
            return self._extract_params_with_regex(query)

    def _parse_llm_response(self, llm_response: str, query: str) -> dict:
        """Parse LLM response to extract swap parameters."""
        json_match = re.search(
            r'\{[^{}]*(?:"token_in_symbol"|"chain")[^{}]*\}', llm_response, re.DOTALL
        )
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                json_match2 = re.search(
                    r'\{.*?"token_in_symbol".*?"token_out_symbol".*?\}',
                    llm_response,
                    re.DOTALL,
                )
                if json_match2:
                    return json.loads(json_match2.group())
        code_block_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", llm_response, re.DOTALL
        )
        if code_block_match:
            return json.loads(code_block_match.group(1))
        return self._extract_params_with_regex(query)

    def _extract_params_with_regex(self, query: str) -> dict:
        """Fallback regex-based parameter extraction."""
        parsed = parse_swap_query(query)
        if not parsed["chain_specified"]:
            return {"requires_chain_selection": True}
        if not parsed["token_in_symbol"]:
            return {"error": "token_in_not_found", "chain": parsed["chain"]}
        if not parsed["token_out_symbol"]:
            return {"error": "token_out_not_found", "chain": parsed["chain"]}
        return parsed
