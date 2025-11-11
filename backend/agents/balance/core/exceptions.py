"""
Custom exceptions for Balance Agent.

Domain-specific exceptions for better error handling.
"""


class BalanceAgentError(Exception):
    """Base exception for Balance Agent errors."""

    pass


class InvalidAddressError(BalanceAgentError):
    """Raised when an invalid address is provided."""

    def __init__(self, address: str, reason: str = ""):
        self.address = address
        self.reason = reason
        message = f"Invalid address: {address}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class ChainNotSupportedError(BalanceAgentError):
    """Raised when an unsupported chain is requested."""

    def __init__(self, chain: str):
        self.chain = chain
        super().__init__(f"Chain not supported: {chain}")


class BalanceFetchError(BalanceAgentError):
    """Raised when balance fetching fails."""

    def __init__(self, chain: str, address: str, reason: str = ""):
        self.chain = chain
        self.address = address
        self.reason = reason
        message = f"Failed to fetch balance for {address} on {chain}"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class ValidationError(BalanceAgentError):
    """Raised when response validation fails."""

    def __init__(self, message: str, details: dict = None):
        self.details = details or {}
        super().__init__(message)
