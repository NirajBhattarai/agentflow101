"""
Polygon liquidity tool - re-exports from shared blockchain module.

This module maintains backward compatibility by re-exporting
the shared liquidity function.
"""

from lib.shared.blockchain.liquidity.polygon import get_liquidity_polygon  # noqa: F401

__all__ = ["get_liquidity_polygon"]
