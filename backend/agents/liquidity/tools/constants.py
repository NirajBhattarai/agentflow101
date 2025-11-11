"""
Constants file - re-exports from shared blockchain module.

This module maintains backward compatibility by re-exporting
constants from the shared blockchain modules.
"""

from lib.shared.blockchain.tokens import (  # noqa: E402, F401
    POLYGON_TOKENS,
    HEDERA_TOKENS,
    CHAIN_TOKENS,
    get_token_address,
)
from lib.shared.blockchain.pools import get_pool_address  # noqa: E402, F401

# These constants don't exist anymore - pools are discovered dynamically
# Keeping placeholders for backward compatibility but they will be empty dicts
POLYGON_POOLS = {}  # Deprecated: Use get_pool_address() instead
HEDERA_POOLS = {}  # Deprecated: Use get_pool_address() instead
CHAIN_POOLS = {}  # Deprecated: Use get_pool_address() instead
