"""
Unit tests for swap executor service.
"""

import pytest
from unittest.mock import patch
from agents.swap.services.swap_executor_service import execute_swap
from agents.swap.core.exceptions import ChainNotSupportedError


class TestSwapExecutorService:
    """Test cases for swap executor service."""

    @patch("agents.swap.services.swap_executor_service.get_swap_hedera")
    @patch("agents.swap.services.swap_executor_service.get_balance_hedera")
    def test_execute_swap_hedera(self, mock_balance, mock_swap):
        """Test executing swap on Hedera."""
        mock_swap.return_value = {
            "token_in_address": "0.0.0",
            "token_out_address": "0.0.456858",
            "token_in_address_evm": "0x0000000000000000000000000000000000000000",
            "token_out_address_evm": "0x000000000000000000000000000000000006f89a",
            "amount_out": "95.0",
            "amount_out_min": "94.5",
            "swap_fee_percent": 0.3,
            "dex_name": "SaucerSwap",
            "router_address": "0x00000000000000000000000000000000006715e6",
        }
        mock_balance.return_value = {
            "balances": [
                {
                    "token_type": "native",
                    "token_symbol": "HBAR",
                    "token_address": "0.0.0",
                    "balance": "100.0",
                }
            ]
        }
        result = execute_swap(
            chain="hedera",
            token_in_symbol="HBAR",
            token_out_symbol="USDC",
            amount_in="0.1",
            account_address="0.0.2",
            slippage_tolerance=0.5,
        )
        assert result["chain"] == "hedera"
        assert result["token_in_symbol"] == "HBAR"
        assert result["token_out_symbol"] == "USDC"
        assert result["amount_in"] == "0.1"
        assert result["account_address"] == "0.0.2"
        assert result["transaction"] is not None
        assert result["transaction"]["chain"] == "hedera"
        assert result["balance_check"] is not None
        assert result["balance_check"]["balance_sufficient"] is True
        assert result["swap_config"] is not None

    @patch("agents.swap.services.swap_executor_service.get_swap_polygon")
    @patch("agents.swap.services.swap_executor_service.get_balance_polygon")
    def test_execute_swap_polygon(self, mock_balance, mock_swap):
        """Test executing swap on Polygon."""
        mock_swap.return_value = {
            "token_in_address": "0x0000000000000000000000000000000000000000",
            "token_out_address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "amount_out": "95.0",
            "amount_out_min": "94.5",
            "swap_fee_percent": 0.3,
            "dex_name": "QuickSwap",
            "router_address": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
        }
        mock_balance.return_value = {
            "balances": [
                {
                    "token_type": "native",
                    "token_symbol": "MATIC",
                    "token_address": "0x0000000000000000000000000000000000000000",
                    "balance": "10.0",
                }
            ]
        }
        result = execute_swap(
            chain="polygon",
            token_in_symbol="MATIC",
            token_out_symbol="USDC",
            amount_in="0.1",
            account_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            slippage_tolerance=0.5,
        )
        assert result["chain"] == "polygon"
        assert result["token_in_symbol"] == "MATIC"
        assert result["token_out_symbol"] == "USDC"
        assert result["amount_in"] == "0.1"
        assert result["transaction"] is not None
        assert result["swap_config"] is not None

    def test_execute_swap_unsupported_chain(self):
        """Test executing swap on unsupported chain."""
        with pytest.raises(ChainNotSupportedError):
            execute_swap(
                chain="ethereum",
                token_in_symbol="ETH",
                token_out_symbol="USDC",
                amount_in="0.1",
                account_address=None,
                slippage_tolerance=0.5,
            )

    @patch("agents.swap.services.swap_executor_service.get_swap_hedera")
    def test_execute_swap_no_account(self, mock_swap):
        """Test executing swap without account address."""
        mock_swap.return_value = {
            "token_in_address": "0.0.0",
            "token_out_address": "0.0.456858",
            "token_in_address_evm": "0x0000000000000000000000000000000000000000",
            "token_out_address_evm": "0x000000000000000000000000000000000006f89a",
            "amount_out": "95.0",
            "amount_out_min": "94.5",
            "swap_fee_percent": 0.3,
            "dex_name": "SaucerSwap",
            "router_address": "0x00000000000000000000000000000000006715e6",
        }
        result = execute_swap(
            chain="hedera",
            token_in_symbol="HBAR",
            token_out_symbol="USDC",
            amount_in="0.1",
            account_address=None,
            slippage_tolerance=0.5,
        )
        assert result["chain"] == "hedera"
        assert result["account_address"] is None
        assert result["balance_check"] is None
        assert result["transaction"] is not None
        assert result["swap_config"] is not None
