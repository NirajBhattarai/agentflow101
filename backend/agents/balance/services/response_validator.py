"""
Response validation services for balance agent.

Handles validation, error handling, and logging for responses.
"""

import json
from ..core.constants import (
    RESPONSE_TYPE,
    CHAIN_UNKNOWN,
    ERROR_EMPTY_RESPONSE,
    ERROR_INVALID_JSON,
    DEFAULT_TOTAL_USD_VALUE,
)


def validate_response_content(content: str) -> str:
    """Validate and fix response content."""
    if not content or not content.strip():
        print("⚠️  Warning: Empty response from agent, using fallback")
        return _build_empty_response()
    try:
        json.loads(content)
        print(f"✅ Validated JSON response: {len(content)} chars")
        return content
    except json.JSONDecodeError as e:
        print(f"⚠️  Warning: Response is not valid JSON: {e}")
        print(f"Response content (first 500 chars): {content[:500]}")
        return _build_invalid_json_response(e, content)


def log_sending_response(content: str) -> None:
    """Log response sending information."""
    print(f"📤 Sending response to event queue: {len(content)} chars")
    print(f"📄 First 100 chars: {content[:100]}")


def _build_empty_response() -> str:
    """Build empty response fallback."""
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "chain": CHAIN_UNKNOWN,
            "account_address": "unknown",
            "balances": [],
            "total_usd_value": DEFAULT_TOTAL_USD_VALUE,
            "error": ERROR_EMPTY_RESPONSE,
        },
        indent=2,
    )


def _build_invalid_json_response(error: Exception, content: str) -> str:
    """Build response for invalid JSON error."""
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "chain": CHAIN_UNKNOWN,
            "account_address": "unknown",
            "balances": [],
            "total_usd_value": DEFAULT_TOTAL_USD_VALUE,
            "error": f"{ERROR_INVALID_JSON}: {str(error)}",
            "raw_response": content[:500],
        },
        indent=2,
    )
