"""
Bridge domain models.

Pydantic models for bridge-related data structures.
"""

from typing import Optional
from pydantic import BaseModel, Field
from ..constants import RESPONSE_TYPE


class BridgeTransaction(BaseModel):
    """Represents a bridge transaction."""

    source_chain: str = Field(description="Source chain (hedera or polygon)")
    destination_chain: str = Field(description="Destination chain (hedera or polygon)")
    token_symbol: str = Field(description="Token symbol to bridge (e.g., USDC, USDT)")
    token_address: str = Field(description="Token address on source chain")
    amount: str = Field(description="Amount to bridge in human-readable format")
    bridge_protocol: str = Field(default="EtaBridge", description="Bridge protocol name")
    bridge_fee: str = Field(description="Bridge fee")
    estimated_time: str = Field(
        description="Estimated bridge time (e.g., '~5 minutes')"
    )
    transaction_hash: Optional[str] = Field(
        default=None, description="Transaction hash if bridge is initiated"
    )
    status: str = Field(description="Bridge status: pending, completed, failed")


class BridgeOption(BaseModel):
    """Represents a bridge option from a protocol."""

    bridge_protocol: str = Field(description="Bridge protocol name")
    bridge_fee: str = Field(description="Bridge fee")
    estimated_time: str = Field(description="Estimated bridge time")
    is_recommended: Optional[bool] = Field(
        default=False, description="Is this the recommended option"
    )


class BridgeBalanceCheck(BaseModel):
    """Represents a balance check result."""

    account_address: str = Field(description="Account address checked")
    token_symbol: str = Field(description="Token symbol")
    balance: str = Field(description="Current balance")
    balance_sufficient: bool = Field(description="Whether balance is sufficient")
    required_amount: str = Field(description="Amount required (including fees)")


class StructuredBridge(BaseModel):
    """Structured bridge response model."""

    type: str = Field(default=RESPONSE_TYPE, description="Response type")
    source_chain: str = Field(description="Source chain (hedera or polygon)")
    destination_chain: str = Field(description="Destination chain (hedera or polygon)")
    token_symbol: str = Field(description="Token symbol to bridge")
    amount: str = Field(description="Amount to bridge")
    account_address: Optional[str] = Field(default=None, description="Account address")
    balance_check: Optional[BridgeBalanceCheck] = Field(
        default=None, description="Balance check result"
    )
    bridge_options: Optional[list[BridgeOption]] = Field(
        default=None, description="Available bridge options"
    )
    transaction: Optional[BridgeTransaction] = Field(
        default=None, description="Bridge transaction details (if initiated)"
    )
    requires_confirmation: Optional[bool] = Field(
        default=False,
        description="Whether explicit confirmation is required due to high amount",
    )
    confirmation_threshold: Optional[float] = Field(
        default=None, description="The threshold amount that requires confirmation"
    )
    amount_exceeds_threshold: Optional[bool] = Field(
        default=False,
        description="Whether the amount exceeds the confirmation threshold",
    )
    error: Optional[str] = Field(default=None, description="Error message if any")

