"""
Balance Agent Definition

Defines the BalanceAgent class that handles balance queries.
"""

import os
from google.adk.agents.llm_agent import LlmAgent  # noqa: E402
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import InMemorySessionService  # noqa: E402
from google.adk.memory.in_memory_memory_service import (
    InMemoryMemoryService,
)  # noqa: E402
from google.adk.artifacts import InMemoryArtifactService  # noqa: E402

from .tools import (  # noqa: E402
    get_balance_polygon,
    get_balance_hedera,
    get_balance_all_chains,
    log_message,
)
from .core.constants import (  # noqa: E402
    DEFAULT_MODEL,
    DEFAULT_USER_ID,
    AGENT_NAME,
    AGENT_DESCRIPTION,
    AGENT_INSTRUCTION,
    ERROR_VALIDATION_FAILED,
)
from .services.query_parser import extract_account_address, parse_chain  # noqa: E402
from .services.response_builder import build_balance_response  # noqa: E402
from .core.response_validator import (  # noqa: E402
    validate_and_serialize_response,
    log_response_info,
    validate_json,
    build_error_response,
)


def _get_model_name() -> str:
    """Get Gemini model name from environment."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def _check_api_keys() -> None:
    """Check if API keys are configured."""
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: No API key found! Set GOOGLE_API_KEY or GEMINI_API_KEY")


def _get_agent_tools() -> list:
    """Get list of tools for the agent."""
    return [
        get_balance_polygon,
        get_balance_hedera,
        get_balance_all_chains,
        log_message,
    ]


class BalanceAgent:
    """Agent that retrieves account balance information from blockchain chains."""

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
        model_name = _get_model_name()
        _check_api_keys()
        return LlmAgent(
            model=model_name,
            name=AGENT_NAME,
            description=AGENT_DESCRIPTION,
            instruction=AGENT_INSTRUCTION,
            tools=_get_agent_tools(),
        )

    async def invoke(self, query: str, session_id: str) -> str:
        """Invoke the agent with a query."""
        print(f"🔍 Balance Agent received query: {query}")
        account_address = extract_account_address(query)
        chain = parse_chain(query, account_address)
        balance_data = build_balance_response(chain, account_address)
        try:
            response = validate_and_serialize_response(balance_data)
            log_response_info(account_address, chain, response)
            validate_json(response)
            return response
        except Exception as e:
            print(f"❌ Validation error: {e}")
            error_msg = f"{ERROR_VALIDATION_FAILED}: {str(e)}"
            return build_error_response(chain, account_address, error_msg)
