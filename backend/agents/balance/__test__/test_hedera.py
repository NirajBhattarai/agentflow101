"""
Unit tests for Hedera balance tool.
Tests fetch actual balance data from Hedera chain using REST API.
"""

import pytest
import requests
from agents.balance.tools.hedera import (
    get_balance_hedera,
    _get_hedera_api_base,
    _parse_hedera_account_id,
)
from agents.balance.tools.constants import HEDERA_TOKENS


class TestHederaBalance:
    """Test cases for Hedera balance fetching."""

    def test_hedera_api_connection(self, rpc_urls):
        """Test that Hedera API endpoint is accessible."""
        api_base = _get_hedera_api_base()
        try:
            # Test basic connectivity
            response = requests.get(f"{api_base}/api/v1/network/stats", timeout=5)
            assert response.status_code in [
                200,
                404,
            ], f"Unexpected status code: {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Could not connect to Hedera API: {e}")

    def test_parse_hedera_account_id(self):
        """Test Hedera account ID parsing."""
        # Valid account IDs
        assert _parse_hedera_account_id("0.0.2") == "0.0.2"
        assert _parse_hedera_account_id("0.0.123456") == "0.0.123456"

        # Invalid account IDs
        with pytest.raises(ValueError):
            _parse_hedera_account_id("invalid")
        with pytest.raises(ValueError):
            _parse_hedera_account_id("0.0")
        with pytest.raises(ValueError):
            _parse_hedera_account_id("0.0.abc")

    def test_native_balance_only(self, rpc_urls, test_account_addresses):
        """Test that native HBAR balance is returned."""
        account = test_account_addresses["hedera"]
        result = get_balance_hedera(account)

        assert result["type"] == "balance"
        assert result["chain"] == "hedera"
        assert result["account_address"] == account
        assert "balances" in result
        assert len(result["balances"]) > 0

        # Check native balance exists
        native_balance = next((b for b in result["balances"] if b["token_type"] == "native"), None)
        assert native_balance is not None, "Native HBAR balance should be present"
        assert native_balance["token_symbol"] == "HBAR"
        assert "balance" in native_balance
        assert "balance_raw" in native_balance
        assert native_balance["decimals"] == 8

    def test_token_balance_with_symbol(
        self, rpc_urls, test_account_addresses, test_token_addresses
    ):
        """Test that token balance is returned when token symbol is provided."""
        account = test_account_addresses["hedera"]
        result = get_balance_hedera(account, token_address="USDC")

        assert result["type"] == "balance"
        assert "balances" in result

        # Token balance might be 0 if account doesn't hold the token
        token_balance = next((b for b in result["balances"] if b["token_type"] == "token"), None)
        if token_balance:
            assert token_balance["token_address"] == HEDERA_TOKENS["USDC"]
            assert "balance" in token_balance
            assert "balance_raw" in token_balance

    def test_token_balance_with_address(
        self, rpc_urls, test_account_addresses, test_token_addresses
    ):
        """Test that token balance is returned when token address is provided."""
        account = test_account_addresses["hedera"]
        token_addr = test_token_addresses["hedera"]["USDC"]
        result = get_balance_hedera(account, token_address=token_addr)

        assert result["type"] == "balance"
        assert "balances" in result

        # Token balance might be 0 if account doesn't hold the token
        token_balance = next((b for b in result["balances"] if b["token_type"] == "token"), None)
        if token_balance:
            assert token_balance["token_address"] == token_addr

    def test_balance_structure(self, rpc_urls, test_account_addresses):
        """Test that balance structure is correct."""
        account = test_account_addresses["hedera"]
        result = get_balance_hedera(account)

        for balance in result["balances"]:
            assert "token_type" in balance
            assert "token_symbol" in balance
            assert "token_address" in balance
            assert "balance" in balance
            assert "balance_raw" in balance
            assert "decimals" in balance

    def test_invalid_account_address(self, rpc_urls):
        """Test that invalid account address returns error."""
        result = get_balance_hedera("invalid_address")

        assert "error" in result or len(result.get("balances", [])) == 0

    def test_balance_formatting(self, rpc_urls, test_account_addresses):
        """Test that balances are properly formatted."""
        account = test_account_addresses["hedera"]
        result = get_balance_hedera(account)

        for balance in result["balances"]:
            # Balance should be a string representation of a float
            balance_value = float(balance["balance"])
            assert balance_value >= 0, "Balance should be non-negative"

            # Balance raw should be a string representation of an integer
            balance_raw_value = int(balance["balance_raw"])
            assert balance_raw_value >= 0, "Balance raw should be non-negative"

    def test_usd_value_included(self, rpc_urls, test_account_addresses):
        """Test that USD value field is included in response."""
        account = test_account_addresses["hedera"]
        result = get_balance_hedera(account)

        assert "total_usd_value" in result
        assert isinstance(result["total_usd_value"], str)
