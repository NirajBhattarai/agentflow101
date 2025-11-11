"""
Constants file - re-exports from shared blockchain module.

This module maintains backward compatibility by re-exporting
all blockchain constants from the shared module.
"""

from lib.shared.blockchain.tokens import (  # noqa: E402, F401
    POLYGON_TOKENS,
    HEDERA_TOKENS,
    HEDERA_TOKEN_EVM_ADDRESSES,
    CHAIN_TOKENS,
    get_token_address,
    hedera_to_evm_address,
)
from lib.shared.blockchain.dex import (  # noqa: E402, F401
    POLYGON_DEX_CONFIG,
    HEDERA_DEX_CONFIG,
    CHAIN_DEX_CONFIG,
    DEFAULT_DEX,
    get_dex_config,
)
from lib.shared.blockchain.networks import (  # noqa: E402, F401
    RPC_URLS,
    EXPLORER_URLS,
    get_chain_rpc_url,
    get_explorer_url,
)
