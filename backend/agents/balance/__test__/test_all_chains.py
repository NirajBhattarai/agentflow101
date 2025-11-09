"""
Unit tests for all chains balance tool.
Tests the aggregation of balances across all chains.
"""

from agents.balance.tools.all_chains import get_balance_all_chains


class TestAllChainsBalance:
    """Test cases for all chains balance aggregation."""

    def test_all_chains_response_structure(self, test_account_addresses):
        """Test that all chains response has correct structure."""
        account = test_account_addresses["polygon"]  # Use Polygon address format
        result = get_balance_all_chains(account)

        assert result["type"] == "balance_summary"
        assert "account_address" in result
        assert "chains" in result
        assert "total_usd_value" in result

    def test_all_chains_includes_all_networks(self, test_account_addresses):
        """Test that all supported chains are included."""
        account = test_account_addresses["polygon"]
        result = get_balance_all_chains(account)
        chains = result["chains"]

        assert "polygon" in chains
        assert "hedera" in chains

    def test_all_chains_account_address_preserved(self, test_account_addresses):
        """Test that account address is preserved in chain results."""
        account = test_account_addresses["polygon"]
        result = get_balance_all_chains(account)
        chains = result["chains"]

        # Polygon should preserve the address
        assert chains["polygon"]["account_address"] == account

        # Hedera might have different address format or error
        # This is expected as Polygon and Hedera use different address formats

    def test_all_chains_balances_exist(self, test_account_addresses):
        """Test that each chain has balances data."""
        account = test_account_addresses["polygon"]
        result = get_balance_all_chains(account)
        chains = result["chains"]

        for chain_name, chain_data in chains.items():
            assert "balances" in chain_data, f"{chain_name} missing balances"
            # Balances might be empty if there's an error, but the key should exist

    def test_all_chains_totals(self, test_account_addresses):
        """Test that totals are calculated and present."""
        account = test_account_addresses["polygon"]
        result = get_balance_all_chains(account)

        assert result["total_usd_value"] is not None
        # Totals should be strings
        assert isinstance(result["total_usd_value"], str)

    def test_all_chains_with_token_address(
        self, test_account_addresses, test_token_addresses
    ):
        """Test that token address is passed to chain tools."""
        account = test_account_addresses["polygon"]
        token_addr = test_token_addresses["polygon"]["USDC"]
        result = get_balance_all_chains(account, token_address=token_addr)

        assert result["token_address"] == token_addr
        # Verify that chains received the token address
        # (actual implementation might vary based on chain-specific handling)
