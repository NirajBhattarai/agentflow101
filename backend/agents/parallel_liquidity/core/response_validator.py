"""
Response validation utilities for Parallel Liquidity Agent.
"""

import json
from .constants import (
    RESPONSE_TYPE,
)
from .models.liquidity import StructuredParallelLiquidity
from .exceptions import ValidationError


def validate_and_serialize_response(liquidity_data: dict) -> str:
    """Validate and serialize liquidity response to JSON."""
    try:
        validated_liquidity = StructuredParallelLiquidity(**liquidity_data)
        return json.dumps(validated_liquidity.model_dump(), indent=2)
    except Exception as e:
        raise ValidationError(
            f"Failed to validate liquidity response: {str(e)}",
            details={"liquidity_data": liquidity_data},
        ) from e


def build_error_response(token_pair: str, error: str) -> str:
    """Build error response."""
    error_data = {
        "type": RESPONSE_TYPE,
        "token_pair": token_pair,
        "chains": {},
        "hedera_pairs": [],
        "polygon_pairs": [],
        "all_pairs": [],
        "error": error,
    }
    return json.dumps(error_data, indent=2)


def log_response_info(token_pair: str, response: str) -> None:
    """Log response information."""
    print(f"✅ Returning liquidity response for {token_pair}")
    print(f"📦 Response length: {len(response)} chars")
    print(f"📄 Response preview: {response[:200]}...")


def validate_json(response: str) -> None:
    """Validate that response is valid JSON."""
    json.loads(response)
