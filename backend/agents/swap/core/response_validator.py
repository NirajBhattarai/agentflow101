"""
Response validation utilities for swap agent.

Handles validation and serialization of swap responses.
"""

import json
from .models.swap import StructuredSwap
from .exceptions import ValidationError


def validate_and_serialize_response(swap_data: dict) -> str:
    """Validate and serialize swap response to JSON."""
    try:
        validated_swap = StructuredSwap(**swap_data)
        return json.dumps(validated_swap.model_dump(), indent=2)
    except Exception as e:
        raise ValidationError(
            f"Failed to validate swap response: {str(e)}",
            details={"swap_data": swap_data},
        ) from e


def build_error_response(chain: str, token_in: str, token_out: str, error: str) -> str:
    """Build error response."""
    from .constants import RESPONSE_TYPE

    error_data = {
        "type": RESPONSE_TYPE,
        "chain": chain,
        "token_in_symbol": token_in,
        "token_out_symbol": token_out,
        "error": error,
    }
    return json.dumps(error_data, indent=2)
