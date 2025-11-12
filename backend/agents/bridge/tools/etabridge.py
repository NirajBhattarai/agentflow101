"""
EtaBridge integration for token bridging between Hedera and Polygon.

EtaBridge is a trustless cross-chain liquidity bridge that enables seamless
token transfers between Hedera and Polygon.
"""

import os
import requests
from typing import Optional, Dict, Any
from lib.shared.blockchain.tokens import get_token_address
from ..core.constants import (
    ETABRIDGE_API_BASE_URL,
    ETABRIDGE_SUPPORTED_CHAINS,
    ETABRIDGE_SUPPORTED_TOKENS,
)
from ..core.exceptions import InvalidBridgePairError, TokenNotSupportedError


def _validate_bridge_request(
    source_chain: str, destination_chain: str, token_symbol: str
) -> None:
    """Validate bridge request parameters."""
    if source_chain == destination_chain:
        raise InvalidBridgePairError(source_chain, destination_chain)
    
    if source_chain not in ETABRIDGE_SUPPORTED_CHAINS:
        raise InvalidBridgePairError(source_chain, destination_chain)
    
    if destination_chain not in ETABRIDGE_SUPPORTED_CHAINS:
        raise InvalidBridgePairError(source_chain, destination_chain)
    
    # EtaBridge only supports USDC
    if token_symbol not in ETABRIDGE_SUPPORTED_TOKENS:
        raise TokenNotSupportedError(
            f"{token_symbol} is not supported. EtaBridge only supports USDC for bridging between Hedera and Polygon."
        )


def _get_chain_id(chain: str) -> int:
    """Get EtaBridge chain ID for a chain."""
    from ..core.constants import ETABRIDGE_CHAIN_IDS
    return ETABRIDGE_CHAIN_IDS.get(chain.lower(), 0)


def _get_token_address(chain: str, token_symbol: str) -> str:
    """Get token address for a chain."""
    try:
        # For Hedera, use EVM address for bridging
        use_evm = chain == "hedera"
        return get_token_address(chain, token_symbol, use_evm=use_evm)
    except Exception as e:
        print(f"⚠️ Error getting token address: {e}")
        return ""


def get_bridge_etabridge(
    source_chain: str,
    destination_chain: str,
    token_symbol: str,
    amount: str,
    account_address: str = "",
) -> Dict[str, Any]:
    """
    Get bridge configuration using EtaBridge.
    
    Args:
        source_chain: Source chain (hedera or polygon)
        destination_chain: Destination chain (hedera or polygon)
        token_symbol: Token symbol to bridge (USDC, USDT, etc.)
        amount: Amount to bridge (human-readable format)
        account_address: Account address (optional)
    
    Returns:
        Dictionary with bridge configuration including addresses, fees, etc.
    """
    _validate_bridge_request(source_chain, destination_chain, token_symbol)
    
    # Get token addresses
    source_token_address = _get_token_address(source_chain, token_symbol)
    destination_token_address = _get_token_address(destination_chain, token_symbol)
    
    # For now, return mock data since EtaBridge API integration may require API keys
    # In production, you would make actual API calls to EtaBridge
    try:
        # Attempt to get quote from EtaBridge API (if available)
        # This is a placeholder - actual implementation would call EtaBridge API
        bridge_fee = "0.1%"  # Default fee
        estimated_time = "~5 minutes"  # Default time
        
        # If EtaBridge API is configured, make actual API call
        etabridge_api_key = os.getenv("ETABRIDGE_API_KEY")
        if etabridge_api_key and ETABRIDGE_API_BASE_URL:
            try:
                # Example API call structure (adjust based on actual EtaBridge API)
                response = requests.post(
                    f"{ETABRIDGE_API_BASE_URL}/quote",
                    json={
                        "source_chain": _get_chain_id(source_chain),
                        "destination_chain": _get_chain_id(destination_chain),
                        "token": token_symbol,
                        "amount": amount,
                    },
                    headers={"Authorization": f"Bearer {etabridge_api_key}"},
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    bridge_fee = data.get("fee", "0.1%")
                    estimated_time = data.get("estimated_time", "~5 minutes")
                elif response.status_code == 400:
                    # Token not supported by EtaBridge
                    raise TokenNotSupportedError(
                        f"{token_symbol} is not supported by EtaBridge. EtaBridge only supports USDC for bridging."
                    )
            except TokenNotSupportedError:
                raise
            except Exception as e:
                print(f"⚠️ EtaBridge API call failed, using defaults: {e}")
        
        from ..core.constants import ETABRIDGE_CONTRACT_ADDRESS, ETABRIDGE_CHAIN_IDS
        
        return {
            "source_chain": source_chain,
            "destination_chain": destination_chain,
            "token_symbol": token_symbol,
            "token_address": source_token_address,
            "destination_token_address": destination_token_address,
            "amount": amount,
            "bridge_fee": bridge_fee,
            "estimated_time": estimated_time,
            "bridge_protocol": "EtaBridge",
            "account_address": account_address,
            "bridge_contract_address": ETABRIDGE_CONTRACT_ADDRESS,
            "source_chain_id": ETABRIDGE_CHAIN_IDS.get(source_chain, 0),
            "destination_chain_id": ETABRIDGE_CHAIN_IDS.get(destination_chain, 0),
        }
    except Exception as e:
        print(f"❌ Error in get_bridge_etabridge: {e}")
        # Return basic configuration even if API call fails
        from ..core.constants import ETABRIDGE_CONTRACT_ADDRESS, ETABRIDGE_CHAIN_IDS
        
        return {
            "source_chain": source_chain,
            "destination_chain": destination_chain,
            "token_symbol": token_symbol,
            "token_address": source_token_address,
            "destination_token_address": destination_token_address,
            "amount": amount,
            "bridge_fee": "0.1%",
            "estimated_time": "~5 minutes",
            "bridge_protocol": "EtaBridge",
            "account_address": account_address,
            "bridge_contract_address": ETABRIDGE_CONTRACT_ADDRESS,
            "source_chain_id": ETABRIDGE_CHAIN_IDS.get(source_chain, 0),
            "destination_chain_id": ETABRIDGE_CHAIN_IDS.get(destination_chain, 0),
        }

