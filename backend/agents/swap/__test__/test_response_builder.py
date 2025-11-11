"""
Unit tests for swap response builder service.
"""

import json
from agents.swap.services.response_builder import (
    build_chain_selection_response,
    build_error_response,
    build_swap_response,
)


class TestResponseBuilder:
    """Test cases for response builder service."""

    def test_build_chain_selection_response(self):
        """Test building chain selection response."""
        response = build_chain_selection_response()
        data = json.loads(response)
        assert data["type"] == "swap"
        assert data["requires_chain_selection"] is True
        assert "hedera" in data["supported_chains"]
        assert "polygon" in data["supported_chains"]

    def test_build_error_response_token_in_not_found(self):
        """Test building error response for missing token in."""
        response = build_error_response("token_in_not_found", "hedera")
        data = json.loads(response)
        assert data["type"] == "swap"
        assert data["chain"] == "hedera"
        assert "error" in data
        assert "token to swap from" in data["error"].lower()

    def test_build_error_response_token_out_not_found(self):
        """Test building error response for missing token out."""
        response = build_error_response("token_out_not_found", "polygon")
        data = json.loads(response)
        assert data["type"] == "swap"
        assert data["chain"] == "polygon"
        assert "error" in data
        assert "token to swap to" in data["error"].lower()

    def test_build_swap_response(self):
        """Test building swap response."""
        swap_data = {
            "chain": "hedera",
            "token_in_symbol": "HBAR",
            "token_out_symbol": "USDC",
            "amount_in": "0.1",
            "account_address": "0.0.123456",
            "balance_check": {
                "account_address": "0.0.123456",
                "token_symbol": "HBAR",
                "balance": "100.00",
                "balance_sufficient": True,
                "required_amount": "0.1",
            },
            "transaction": {
                "chain": "hedera",
                "token_in_symbol": "HBAR",
                "amount_in": "0.1",
                "amount_out": "95.0",
                "status": "pending",
            },
        }
        response = build_swap_response(swap_data)
        assert response["type"] == "swap"
        assert response["chain"] == "hedera"
        assert response["token_in_symbol"] == "HBAR"
        assert response["token_out_symbol"] == "USDC"
        assert response["amount_in"] == "0.1"
        assert response["transaction"] is not None
        assert response["requires_confirmation"] is False
        assert isinstance(response, dict)  # Returns dict, not JSON string
