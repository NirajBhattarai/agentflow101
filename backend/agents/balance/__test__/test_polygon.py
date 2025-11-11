"""
Unit tests for Polygon balance tool.
Tests fetch actual balance data from Polygon chain using Web3.
"""

from web3 import Web3
from agents.balance.tools.polygon import get_balance_polygon, _get_web3_instance
from lib.shared.blockchain.tokens.constants import POLYGON_TOKENS


class TestPolygonBalance:
    """Test cases for Polygon balance fetching."""

    def test_web3_connection(self, rpc_urls):
        """Test that Web3 can connect to Polygon RPC."""
        w3 = _get_web3_instance()
        assert w3.is_connected(), "Failed to connect to Polygon RPC"

        # Test that we can get latest block
        latest_block = w3.eth.block_number
        assert latest_block > 0, "Should be able to get block number"

    def test_all_token_balances(self, rpc_urls, test_account_addresses):
        """Test that all token balances are returned when no token_address provided."""
        account = test_account_addresses["polygon"]
        result = get_balance_polygon(account)

        assert result["type"] == "balance"
        assert result["chain"] == "polygon"
        assert result["account_address"] == Web3.to_checksum_address(account)
        assert "balances" in result
        assert len(result["balances"]) > 0

        # Check native balance exists
        native_balance = next(
            (b for b in result["balances"] if b["token_type"] == "native"), None
        )
        assert native_balance is not None, "Native MATIC balance should be present"
        assert native_balance["token_symbol"] == "MATIC"
        assert "balance" in native_balance
        assert "balance_raw" in native_balance
        assert native_balance["decimals"] == 18

        # Check that all tokens from POLYGON_TOKENS are included
        token_balances = [b for b in result["balances"] if b["token_type"] == "token"]
        assert len(token_balances) == len(POLYGON_TOKENS), (
            f"Should return balances for all {len(POLYGON_TOKENS)} tokens"
        )

        # Verify all token addresses from constants are present
        expected_addresses = {
            Web3.to_checksum_address(token_data["address"]) 
            for token_data in POLYGON_TOKENS.values()
        }
        actual_addresses = {
            Web3.to_checksum_address(b["token_address"]) for b in token_balances
        }
        assert expected_addresses == actual_addresses, (
            "All token addresses from POLYGON_TOKENS should be present"
        )

    def test_token_balance_with_symbol(
        self, rpc_urls, test_account_addresses, test_token_addresses
    ):
        """Test that token balance is returned when token symbol is provided."""
        account = test_account_addresses["polygon"]
        result = get_balance_polygon(account, token_address="USDC")

        assert result["type"] == "balance"
        assert "balances" in result

        # Should have native balance + 1 token balance
        assert len(result["balances"]) == 2, "Should have native + 1 token balance"

        # Check native balance exists
        native_balance = next(
            (b for b in result["balances"] if b["token_type"] == "native"), None
        )
        assert native_balance is not None, "Native MATIC balance should be present"

        # Check token balance exists
        token_balance = next(
            (b for b in result["balances"] if b["token_type"] == "token"), None
        )
        assert token_balance is not None, "Token balance should be present"
        assert token_balance["token_address"] == Web3.to_checksum_address(
            POLYGON_TOKENS["USDC"]["address"]
        )
        assert "balance" in token_balance
        assert "balance_raw" in token_balance

    def test_token_balance_with_address(
        self, rpc_urls, test_account_addresses, test_token_addresses
    ):
        """Test that token balance is returned when token address is provided."""
        account = test_account_addresses["polygon"]
        token_addr = test_token_addresses["polygon"]["USDC"]
        result = get_balance_polygon(account, token_address=token_addr)

        assert result["type"] == "balance"
        assert "balances" in result

        # Should have native balance + 1 token balance
        assert len(result["balances"]) == 2, "Should have native + 1 token balance"

        # Check native balance exists
        native_balance = next(
            (b for b in result["balances"] if b["token_type"] == "native"), None
        )
        assert native_balance is not None, "Native MATIC balance should be present"

        # Check token balance exists
        token_balance = next(
            (b for b in result["balances"] if b["token_type"] == "token"), None
        )
        assert token_balance is not None, "Token balance should be present"
        assert token_balance["token_address"] == Web3.to_checksum_address(token_addr)

    def test_balance_structure(self, rpc_urls, test_account_addresses):
        """Test that balance structure is correct."""
        account = test_account_addresses["polygon"]
        result = get_balance_polygon(account)

        for balance in result["balances"]:
            assert "token_type" in balance
            assert "token_symbol" in balance
            assert "token_address" in balance
            assert "balance" in balance
            assert "balance_raw" in balance
            assert "decimals" in balance

    def test_invalid_account_address(self, rpc_urls):
        """Test that invalid account address returns error."""
        result = get_balance_polygon("invalid_address")

        assert "error" in result or len(result.get("balances", [])) == 0

    def test_balance_formatting(self, rpc_urls, test_account_addresses):
        """Test that balances are properly formatted."""
        account = test_account_addresses["polygon"]
        result = get_balance_polygon(account)

        for balance in result["balances"]:
            # Balance should be a string representation of a float
            balance_value = float(balance["balance"])
            assert balance_value >= 0, "Balance should be non-negative"

            # Balance raw should be a string representation of an integer
            balance_raw_value = int(balance["balance_raw"])
            assert balance_raw_value >= 0, "Balance raw should be non-negative"

    def test_usd_value_included(self, rpc_urls, test_account_addresses):
        """Test that USD value field is included in response."""
        account = test_account_addresses["polygon"]
        result = get_balance_polygon(account)

        assert "total_usd_value" in result
        assert isinstance(result["total_usd_value"], str)

    def test_all_tokens_in_constants_fetched(self, rpc_urls, test_account_addresses):
        """Test that all tokens defined in POLYGON_TOKENS are fetched."""
        account = test_account_addresses["polygon"]
        result = get_balance_polygon(account)

        token_balances = [b for b in result["balances"] if b["token_type"] == "token"]

        # Verify we have entries for all tokens (even if balance is 0)
        assert len(token_balances) == len(POLYGON_TOKENS), (
            f"Expected {len(POLYGON_TOKENS)} token balances, got {len(token_balances)}"
        )

        # Verify each token from constants has a corresponding balance entry
        for symbol, token_data in POLYGON_TOKENS.items():
            # POLYGON_TOKENS now contains dictionaries, extract address
            address = token_data["address"]
            checksum_address = Web3.to_checksum_address(address)
            token_entry = next(
                (
                    b
                    for b in token_balances
                    if Web3.to_checksum_address(b["token_address"]) == checksum_address
                ),
                None,
            )
            assert token_entry is not None, (
                f"Token {symbol} ({address}) should have a balance entry"
            )

    def test_token_balance_handles_errors_gracefully(
        self, rpc_urls, test_account_addresses
    ):
        """Test that errors fetching individual tokens don't break the entire request."""
        account = test_account_addresses["polygon"]
        result = get_balance_polygon(account)

        # Should still return results even if some tokens fail
        assert "balances" in result
        assert len(result["balances"]) > 0

        # Check that all balance entries have required fields
        for balance in result["balances"]:
            assert "token_type" in balance
            assert "token_symbol" in balance
            assert "token_address" in balance
            assert "balance" in balance
            assert "balance_raw" in balance
            # Error field is optional, but if present, balance should be "0"
            if "error" in balance:
                assert balance["balance"] == "0"
                assert balance["balance_raw"] == "0"
