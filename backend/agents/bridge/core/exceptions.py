"""
Custom exceptions for Bridge Agent.
"""


class ChainNotSupportedError(Exception):
    """Raised when a chain is not supported."""

    def __init__(self, chain: str):
        self.chain = chain
        super().__init__(f"Chain '{chain}' is not supported for bridging")


class InvalidBridgePairError(Exception):
    """Raised when bridge pair is invalid."""

    def __init__(self, source: str, destination: str):
        self.source = source
        self.destination = destination
        super().__init__(
            f"Invalid bridge pair: {source} -> {destination}. Only Hedera <-> Polygon supported"
        )


class TokenNotSupportedError(Exception):
    """Raised when a token is not supported for bridging."""

    def __init__(self, token: str):
        self.token = token
        super().__init__(f"Token '{token}' is not supported for bridging")

