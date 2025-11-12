"""
Response validation utilities for bridge agent.
"""

import json
from typing import Any
from .constants import (
    RESPONSE_TYPE,
    ERROR_VALIDATION_FAILED,
    ERROR_INVALID_JSON,
)


def validate_and_serialize_response(response_data: dict) -> str:
    """
    Validate and serialize response data.
    
    Args:
        response_data: Response data dictionary
    
    Returns:
        JSON string
    """
    try:
        # Ensure type is set
        if "type" not in response_data:
            response_data["type"] = RESPONSE_TYPE
        
        # Validate required fields
        required_fields = ["source_chain", "destination_chain", "token_symbol", "amount"]
        for field in required_fields:
            if field not in response_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Serialize to JSON
        return json.dumps(response_data, indent=2)
    except Exception as e:
        print(f"❌ Validation error: {e}")
        error_response = {
            "type": RESPONSE_TYPE,
            "error": f"{ERROR_VALIDATION_FAILED}: {str(e)}",
        }
        return json.dumps(error_response, indent=2)

