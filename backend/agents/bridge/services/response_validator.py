"""
Response validation utilities for bridge agent services.
"""

import json
from ..core.constants import (
    RESPONSE_TYPE,
    ERROR_EMPTY_RESPONSE,
)


def validate_response_content(content: str) -> str:
    """
    Validate response content.
    
    Args:
        content: Response content string
    
    Returns:
        Validated content string
    """
    if not content or not content.strip():
        return json.dumps(
            {
                "type": RESPONSE_TYPE,
                "error": ERROR_EMPTY_RESPONSE,
            },
            indent=2,
        )
    return content


def log_sending_response(content: str) -> None:
    """Log that response is being sent."""
    print(f"📤 Sending bridge response (length: {len(content)})")


def build_execution_error_response(error: Exception) -> str:
    """Build error response for execution errors."""
    return json.dumps(
        {
            "type": RESPONSE_TYPE,
            "error": f"Execution error: {str(error)}",
        },
        indent=2,
    )

