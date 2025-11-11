"""
Unit tests for swap query parser service.
"""

from agents.swap.services.query_parser import (
    extract_account_address,
    extract_chain,
    extract_token_symbols,
    extract_amount,
    extract_slippage,
    parse_swap_query,
)


class TestQueryParser:
    """Test cases for query parser service."""

    def test_extract_account_address_hedera(self):
        """Test extracting Hedera address."""
        query = "Swap 0.1 HBAR to USDC for account 0.0.123456"
        address = extract_account_address(query)
        assert address == "0.0.123456"

    def test_extract_account_address_evm(self):
        """Test extracting EVM address."""
        query = "Swap 0.1 MATIC to USDC for account 0x1234567890123456789012345678901234567890"
        address = extract_account_address(query)
        assert address == "0x1234567890123456789012345678901234567890"

    def test_extract_account_address_none(self):
        """Test extracting address when none present."""
        query = "Swap 0.1 HBAR to USDC"
        address = extract_account_address(query)
        assert address is None

    def test_extract_chain_hedera(self):
        """Test extracting Hedera chain."""
        query = "Swap 0.1 HBAR to USDC on Hedera"
        chain, specified = extract_chain(query)
        assert chain == "hedera"
        assert specified is True

    def test_extract_chain_polygon(self):
        """Test extracting Polygon chain."""
        query = "Swap 0.1 MATIC to USDC on Polygon"
        chain, specified = extract_chain(query)
        assert chain == "polygon"
        assert specified is True

    def test_extract_chain_default(self):
        """Test default chain when not specified."""
        query = "Swap 0.1 HBAR to USDC"
        chain, specified = extract_chain(query)
        assert chain == "hedera"  # Default
        assert specified is False

    def test_extract_token_symbols_with_to(self):
        """Test extracting tokens with 'to' keyword."""
        query = "Swap 0.1 HBAR to USDC"
        token_in, token_out = extract_token_symbols(query, "hedera", True)
        assert token_in == "HBAR"
        assert token_out == "USDC"

    def test_extract_token_symbols_with_for(self):
        """Test extracting tokens with 'for' keyword."""
        query = "Swap 0.1 USDC for HBAR"
        token_in, token_out = extract_token_symbols(query, "hedera", True)
        assert token_in == "USDC"
        assert token_out == "HBAR"

    def test_extract_amount(self):
        """Test extracting amount."""
        query = "Swap 0.5 HBAR to USDC"
        amount = extract_amount(query)
        assert amount == "0.5"

    def test_extract_amount_default(self):
        """Test default amount when not specified."""
        query = "Swap HBAR to USDC"
        amount = extract_amount(query)
        assert amount == "0.01"  # Default

    def test_extract_slippage(self):
        """Test extracting slippage tolerance."""
        query = "Swap 0.1 HBAR to USDC with slippage 1.0"
        slippage = extract_slippage(query)
        assert slippage == 1.0

    def test_extract_slippage_default(self):
        """Test default slippage when not specified."""
        query = "Swap 0.1 HBAR to USDC"
        slippage = extract_slippage(query)
        assert slippage == 0.5  # Default

    def test_parse_swap_query_complete(self):
        """Test parsing complete swap query."""
        query = (
            "Swap 0.1 HBAR to USDC on Hedera for account 0.0.123456 with slippage 1.0"
        )
        params = parse_swap_query(query)
        assert params["chain"] == "hedera"
        assert params["chain_specified"] is True
        assert params["token_in_symbol"] == "HBAR"
        assert params["token_out_symbol"] == "USDC"
        assert params["amount_in"] == "0.1"
        assert params["account_address"] == "0.0.123456"
        assert params["slippage_tolerance"] == 1.0

    def test_parse_swap_query_minimal(self):
        """Test parsing minimal swap query."""
        query = "Swap HBAR to USDC"
        params = parse_swap_query(query)
        assert params["chain"] == "hedera"
        assert params["token_in_symbol"] == "HBAR"
        assert params["token_out_symbol"] == "USDC"
        assert params["amount_in"] == "0.01"  # Default
        assert params["slippage_tolerance"] == 0.5  # Default
