"""
Response validation utilities for swap agent.

Handles validation, error handling, and logging for responses.
"""

import json
from ..core.constants import (
    RESPONSE_TYPE,
    CHAIN_UNKNOWN,
    ERROR_EMPTY_RESPONSE,
    ERROR_INVALID_JSON,
    ERROR_EXECUTION_ERROR,
)


def validate_response_content(content: str) -> str:
    """Validate and fix response content."""
    if not content or not content.strip():
        return _build_empty_response()
    try:
        json.loads(content)
        print(f"✅ Validated JSON response: {len(content)} chars")
        return content
    except json.JSONDecodeError as e:
        print(f"⚠️  Warning: Response is not valid JSON: {e}")
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
            "token_in_symbol": "unknown",
            "token_out_symbol": "unknown",
            "amount_in": "0",
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
            "token_in_symbol": "unknown",
            "token_out_symbol": "unknown",
            "amount_in": "0",
            "error": f"{ERROR_INVALID_JSON}: {str(error)}",
            "raw_response": content[:500],
        },
        indent=2,
    )


def build_execution_error_response(error: Exception) -> str:
    """Build response for execution error."""
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "chain": CHAIN_UNKNOWN,
            "token_in_symbol": "unknown",
            "token_out_symbol": "unknown",
            "amount_in": "0",
            "error": f"{ERROR_EXECUTION_ERROR}: {str(error)}",
        },
        indent=2,
    )
