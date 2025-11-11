"""
Hardcoded mock data layer for Market Insights Agent.
Provides realistic CoinGecko-like responses for demo purposes.
"""

from typing import Dict, Any, Optional, List


# Hardcoded pool data for different networks
MOCK_POOL_DATA: Dict[str, Dict[str, Any]] = {
    "eth": {
        "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640": {  # USDC/WETH pool
            "data": {
                "type": "pool",
                "id": "eth-0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                "attributes": {
                    "address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                    "base_token": {
                        "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                        "symbol": "USDC",
                        "name": "USD Coin",
                        "liquidity_usd": 250000000.0
                    },
                    "quote_token": {
                        "address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                        "symbol": "WETH",
                        "name": "Wrapped Ether",
                        "liquidity_usd": 250000000.0
                    },
                    "reserve_in_usd": 500000000.0,
                    "volume_usd": {"h24": 45000000.0},
                    "price_usd": 0.0004,
                    "price_change_percentage": {"h24": 2.5}
                }
            }
        },
        "0x4e68ccd3e89f51c3070d598798e3a479f8a38724": {  # WETH/USDT pool
            "data": {
                "type": "pool",
                "id": "eth-0x4e68ccd3e89f51c3070d598798e3a479f8a38724",
                "attributes": {
                    "address": "0x4e68ccd3e89f51c3070d598798e3a479f8a38724",
                    "base_token": {
                        "address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                        "symbol": "WETH",
                        "name": "Wrapped Ether",
                        "liquidity_usd": 180000000.0
                    },
                    "quote_token": {
                        "address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
                        "symbol": "USDT",
                        "name": "Tether USD",
                        "liquidity_usd": 180000000.0
                    },
                    "reserve_in_usd": 360000000.0,
                    "volume_usd": {"h24": 32000000.0},
                    "price_usd": 0.00035,
                    "price_change_percentage": {"h24": 1.8}
                }
            }
        }
    },
    "polygon": {
        "0x4ccd010148379ea5318b56e3e3c9b3b8b1d1c77c": {  # USDT/WETH pool
            "data": {
                "type": "pool",
                "id": "polygon-0x4ccd010148379ea5318b56e3e3c9b3b8b1d1c77c",
                "attributes": {
                    "address": "0x4ccd010148379ea5318b56e3e3c9b3b8b1d1c77c",
                    "base_token": {
                        "address": "0xc2132d05d31c914a87c6611c10748aeb04b58e8f",
                        "symbol": "USDT",
                        "name": "Tether USD",
                        "liquidity_usd": 120000000.0
                    },
                    "quote_token": {
                        "address": "0x7ceb23fd6fc0adc59d0b4f286ed88c46ccca134a",
                        "symbol": "WETH",
                        "name": "Wrapped Ether",
                        "liquidity_usd": 120000000.0
                    },
                    "reserve_in_usd": 240000000.0,
                    "volume_usd": {"h24": 18000000.0},
                    "price_usd": 0.00042,
                    "price_change_percentage": {"h24": 3.2}
                }
            }
        },
        "0x45dda9cb7c25131df268515131f647d726f50608": {  # USDC/WETH pool
            "data": {
                "type": "pool",
                "id": "polygon-0x45dda9cb7c25131df268515131f647d726f50608",
                "attributes": {
                    "address": "0x45dda9cb7c25131df268515131f647d726f50608",
                    "base_token": {
                        "address": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
                        "symbol": "USDC",
                        "name": "USD Coin",
                        "liquidity_usd": 95000000.0
                    },
                    "quote_token": {
                        "address": "0x7ceb23fd6fc0adc59d0b4f286ed88c46ccca134a",
                        "symbol": "WETH",
                        "name": "Wrapped Ether",
                        "liquidity_usd": 95000000.0
                    },
                    "reserve_in_usd": 190000000.0,
                    "volume_usd": {"h24": 15000000.0},
                    "price_usd": 0.00041,
                    "price_change_percentage": {"h24": 2.1}
                }
            }
        }
    },
    "hedera": {
        "0.0.123456": {  # USDC/HBAR pool
            "data": {
                "type": "pool",
                "id": "hedera-0.0.123456",
                "attributes": {
                    "address": "0.0.123456",
                    "base_token": {
                        "address": "0.0.456789",
                        "symbol": "USDC",
                        "name": "USD Coin",
                        "liquidity_usd": 45000000.0
                    },
                    "quote_token": {
                        "address": "0.0.0",
                        "symbol": "HBAR",
                        "name": "Hedera",
                        "liquidity_usd": 45000000.0
                    },
                    "reserve_in_usd": 90000000.0,
                    "volume_usd": {"h24": 8500000.0},
                    "price_usd": 0.05,
                    "price_change_percentage": {"h24": 1.5}
                }
            }
        },
        "0.0.234567": {  # USDT/HBAR pool
            "data": {
                "type": "pool",
                "id": "hedera-0.0.234567",
                "attributes": {
                    "address": "0.0.234567",
                    "base_token": {
                        "address": "0.0.567890",
                        "symbol": "USDT",
                        "name": "Tether USD",
                        "liquidity_usd": 38000000.0
                    },
                    "quote_token": {
                        "address": "0.0.0",
                        "symbol": "HBAR",
                        "name": "Hedera",
                        "liquidity_usd": 38000000.0
                    },
                    "reserve_in_usd": 76000000.0,
                    "volume_usd": {"h24": 7200000.0},
                    "price_usd": 0.049,
                    "price_change_percentage": {"h24": 1.2}
                }
            }
        }
    }
}

# Hardcoded token data
MOCK_TOKEN_DATA: Dict[str, Dict[str, Any]] = {
    "eth": {
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {  # WETH
            "data": {
                "type": "token",
                "id": "eth-0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "attributes": {
                    "address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                    "symbol": "WETH",
                    "name": "Wrapped Ether",
                    "total_reserve_in_usd": 850000000.0,
                    "price_usd": 2500.0,
                    "volume_usd": {"h24": 125000000.0},
                    "price_change_percentage": {"h24": 2.8}
                }
            },
            "included": [
                {
                    "type": "pool",
                    "id": "eth-0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                    "attributes": {
                        "address": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                        "base_token": {"address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"},
                        "quote_token": {"address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"},
                        "reserve_in_usd": 500000000.0,
                        "volume_usd": {"h24": 45000000.0},
                        "price_usd": 0.0004
                    }
                },
                {
                    "type": "pool",
                    "id": "eth-0x4e68ccd3e89f51c3070d598798e3a479f8a38724",
                    "attributes": {
                        "address": "0x4e68ccd3e89f51c3070d598798e3a479f8a38724",
                        "base_token": {"address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"},
                        "quote_token": {"address": "0xdac17f958d2ee523a2206206994597c13d831ec7"},
                        "reserve_in_usd": 360000000.0,
                        "volume_usd": {"h24": 32000000.0},
                        "price_usd": 0.00035
                    }
                }
            ]
        },
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {  # USDC
            "data": {
                "type": "token",
                "id": "eth-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                "attributes": {
                    "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                    "symbol": "USDC",
                    "name": "USD Coin",
                    "total_reserve_in_usd": 1200000000.0,
                    "price_usd": 1.0,
                    "volume_usd": {"h24": 250000000.0},
                    "price_change_percentage": {"h24": 0.1}
                }
            },
            "included": []
        }
    },
    "polygon": {
        "0x7ceb23fd6fc0adc59d0b4f286ed88c46ccca134a": {  # WETH
            "data": {
                "type": "token",
                "id": "polygon-0x7ceb23fd6fc0adc59d0b4f286ed88c46ccca134a",
                "attributes": {
                    "address": "0x7ceb23fd6fc0adc59d0b4f286ed88c46ccca134a",
                    "symbol": "WETH",
                    "name": "Wrapped Ether",
                    "total_reserve_in_usd": 320000000.0,
                    "price_usd": 2500.0,
                    "volume_usd": {"h24": 48000000.0},
                    "price_change_percentage": {"h24": 2.5}
                }
            },
            "included": [
                {
                    "type": "pool",
                    "id": "polygon-0x4ccd010148379ea5318b56e3e3c9b3b8b1d1c77c",
                    "attributes": {
                        "address": "0x4ccd010148379ea5318b56e3e3c9b3b8b1d1c77c",
                        "base_token": {"address": "0xc2132d05d31c914a87c6611c10748aeb04b58e8f"},
                        "quote_token": {"address": "0x7ceb23fd6fc0adc59d0b4f286ed88c46ccca134a"},
                        "reserve_in_usd": 240000000.0,
                        "volume_usd": {"h24": 18000000.0},
                        "price_usd": 0.00042
                    }
                }
            ]
        }
    },
    "hedera": {
        "0.0.0": {  # HBAR
            "data": {
                "type": "token",
                "id": "hedera-0.0.0",
                "attributes": {
                    "address": "0.0.0",
                    "symbol": "HBAR",
                    "name": "Hedera",
                    "total_reserve_in_usd": 165000000.0,
                    "price_usd": 0.05,
                    "volume_usd": {"h24": 15700000.0},
                    "price_change_percentage": {"h24": 1.3}
                }
            },
            "included": [
                {
                    "type": "pool",
                    "id": "hedera-0.0.123456",
                    "attributes": {
                        "address": "0.0.123456",
                        "base_token": {"address": "0.0.456789"},
                        "quote_token": {"address": "0.0.0"},
                        "reserve_in_usd": 90000000.0,
                        "volume_usd": {"h24": 8500000.0},
                        "price_usd": 0.05
                    }
                }
            ]
        }
    }
}

# Hardcoded token prices
MOCK_TOKEN_PRICES: Dict[str, Dict[str, Any]] = {
    "eth": {
        "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {  # WETH
            "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {
                "usd": 2500.0,
                "usd_24h_change": 2.8
            }
        },
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {  # USDC
            "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": {
                "usd": 1.0,
                "usd_24h_change": 0.1
            }
        },
        "0xdac17f958d2ee523a2206206994597c13d831ec7": {  # USDT
            "0xdac17f958d2ee523a2206206994597c13d831ec7": {
                "usd": 0.9998,
                "usd_24h_change": -0.05
            }
        }
    },
    "polygon": {
        "0x7ceb23fd6fc0adc59d0b4f286ed88c46ccca134a": {  # WETH
            "0x7ceb23fd6fc0adc59d0b4f286ed88c46ccca134a": {
                "usd": 2500.0,
                "usd_24h_change": 2.5
            }
        },
        "0x2791bca1f2de4661ed88a30c99a7a9449aa84174": {  # USDC
            "0x2791bca1f2de4661ed88a30c99a7a9449aa84174": {
                "usd": 1.0,
                "usd_24h_change": 0.1
            }
        }
    },
    "hedera": {
        "0.0.0": {  # HBAR
            "0.0.0": {
                "usd": 0.05,
                "usd_24h_change": 1.3
            }
        },
        "0.0.456789": {  # USDC
            "0.0.456789": {
                "usd": 1.0,
                "usd_24h_change": 0.1
            }
        }
    }
}

# Hardcoded trending tokens data
MOCK_TRENDING_TOKENS: Dict[str, List[Dict[str, Any]]] = {
    "all": [
        # Ethereum trending tokens
        {
            "type": "token",
            "id": "eth-0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "attributes": {
                "address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "symbol": "WETH",
                "name": "Wrapped Ether",
                "network_id": "eth",
                "price_usd": 2500.0,
                "volume_usd": {"h24": 125000000.0},
                "total_reserve_in_usd": 850000000.0,
                "price_change_percentage": {"h24": 2.8}
            }
        },
        {
            "type": "token",
            "id": "eth-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "attributes": {
                "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                "symbol": "USDC",
                "name": "USD Coin",
                "network_id": "eth",
                "price_usd": 1.0,
                "volume_usd": {"h24": 250000000.0},
                "total_reserve_in_usd": 1200000000.0,
                "price_change_percentage": {"h24": 0.1}
            }
        },
        # Polygon trending tokens
        {
            "type": "token",
            "id": "polygon-0x7ceb23fd6fc0adc59d0b4f286ed88c46ccca134a",
            "attributes": {
                "address": "0x7ceb23fd6fc0adc59d0b4f286ed88c46ccca134a",
                "symbol": "WETH",
                "name": "Wrapped Ether",
                "network_id": "polygon",
                "price_usd": 2500.0,
                "volume_usd": {"h24": 48000000.0},
                "total_reserve_in_usd": 320000000.0,
                "price_change_percentage": {"h24": 2.5}
            }
        },
        {
            "type": "token",
            "id": "polygon-0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",
            "attributes": {
                "address": "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",
                "symbol": "MATIC",
                "name": "Polygon",
                "network_id": "polygon",
                "price_usd": 0.75,
                "volume_usd": {"h24": 35000000.0},
                "total_reserve_in_usd": 280000000.0,
                "price_change_percentage": {"h24": 4.5}
            }
        },
        {
            "type": "token",
            "id": "polygon-0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
            "attributes": {
                "address": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
                "symbol": "USDC",
                "name": "USD Coin",
                "network_id": "polygon",
                "price_usd": 1.0,
                "volume_usd": {"h24": 18000000.0},
                "total_reserve_in_usd": 150000000.0,
                "price_change_percentage": {"h24": 0.1}
            }
        },
        # Hedera trending tokens (SaucerSwap)
        {
            "type": "token",
            "id": "hedera-0.0.0",
            "attributes": {
                "address": "0.0.0",
                "symbol": "HBAR",
                "name": "Hedera",
                "network_id": "hedera",
                "price_usd": 0.05,
                "volume_usd": {"h24": 15700000.0},
                "total_reserve_in_usd": 165000000.0,
                "price_change_percentage": {"h24": 1.3}
            }
        },
        {
            "type": "token",
            "id": "hedera-0.0.678901",
            "attributes": {
                "address": "0.0.678901",
                "symbol": "SAUCE",
                "name": "SaucerSwap Token",
                "network_id": "hedera",
                "price_usd": 0.12,
                "volume_usd": {"h24": 5200000.0},
                "total_reserve_in_usd": 45000000.0,
                "price_change_percentage": {"h24": 5.8}
            }
        },
        {
            "type": "token",
            "id": "hedera-0.0.456789",
            "attributes": {
                "address": "0.0.456789",
                "symbol": "USDC",
                "name": "USD Coin",
                "network_id": "hedera",
                "price_usd": 1.0,
                "volume_usd": {"h24": 8500000.0},
                "total_reserve_in_usd": 90000000.0,
                "price_change_percentage": {"h24": 0.1}
            }
        }
    ],
    "eth": [
        {
            "type": "token",
            "id": "eth-0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "attributes": {
                "address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
                "symbol": "WETH",
                "name": "Wrapped Ether",
                "network_id": "eth",
                "price_usd": 2500.0,
                "volume_usd": {"h24": 125000000.0},
                "total_reserve_in_usd": 850000000.0,
                "price_change_percentage": {"h24": 2.8}
            }
        },
        {
            "type": "token",
            "id": "eth-0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "attributes": {
                "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                "symbol": "USDC",
                "name": "USD Coin",
                "network_id": "eth",
                "price_usd": 1.0,
                "volume_usd": {"h24": 250000000.0},
                "total_reserve_in_usd": 1200000000.0,
                "price_change_percentage": {"h24": 0.1}
            }
        }
    ],
    "polygon": [
        {
            "type": "token",
            "id": "polygon-0x7ceb23fd6fc0adc59d0b4f286ed88c46ccca134a",
            "attributes": {
                "address": "0x7ceb23fd6fc0adc59d0b4f286ed88c46ccca134a",
                "symbol": "WETH",
                "name": "Wrapped Ether",
                "network_id": "polygon",
                "price_usd": 2500.0,
                "volume_usd": {"h24": 48000000.0},
                "total_reserve_in_usd": 320000000.0,
                "price_change_percentage": {"h24": 2.5}
            }
        },
        {
            "type": "token",
            "id": "polygon-0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",
            "attributes": {
                "address": "0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270",
                "symbol": "MATIC",
                "name": "Polygon",
                "network_id": "polygon",
                "price_usd": 0.75,
                "volume_usd": {"h24": 35000000.0},
                "total_reserve_in_usd": 280000000.0,
                "price_change_percentage": {"h24": 4.5}
            }
        },
        {
            "type": "token",
            "id": "polygon-0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
            "attributes": {
                "address": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
                "symbol": "USDC",
                "name": "USD Coin",
                "network_id": "polygon",
                "price_usd": 1.0,
                "volume_usd": {"h24": 18000000.0},
                "total_reserve_in_usd": 150000000.0,
                "price_change_percentage": {"h24": 0.1}
            }
        }
    ],
    "hedera": [
        {
            "type": "token",
            "id": "hedera-0.0.0",
            "attributes": {
                "address": "0.0.0",
                "symbol": "HBAR",
                "name": "Hedera",
                "network_id": "hedera",
                "price_usd": 0.05,
                "volume_usd": {"h24": 15700000.0},
                "total_reserve_in_usd": 165000000.0,
                "price_change_percentage": {"h24": 1.3}
            }
        },
        {
            "type": "token",
            "id": "hedera-0.0.678901",
            "attributes": {
                "address": "0.0.678901",
                "symbol": "SAUCE",
                "name": "SaucerSwap Token",
                "network_id": "hedera",
                "price_usd": 0.12,
                "volume_usd": {"h24": 5200000.0},
                "total_reserve_in_usd": 45000000.0,
                "price_change_percentage": {"h24": 5.8}
            }
        },
        {
            "type": "token",
            "id": "hedera-0.0.456789",
            "attributes": {
                "address": "0.0.456789",
                "symbol": "USDC",
                "name": "USD Coin",
                "network_id": "hedera",
                "price_usd": 1.0,
                "volume_usd": {"h24": 8500000.0},
                "total_reserve_in_usd": 90000000.0,
                "price_change_percentage": {"h24": 0.1}
            }
        }
    ]
}


def get_mock_pool_data(network: str, pool_address: str) -> Optional[Dict[str, Any]]:
    """Get mock pool data for a given network and pool address."""
    network_key = network.lower() if network else "eth"
    if network_key in MOCK_POOL_DATA:
        # Try exact match first
        if pool_address in MOCK_POOL_DATA[network_key]:
            return MOCK_POOL_DATA[network_key][pool_address]
        # Try case-insensitive match
        pool_lower = pool_address.lower()
        for key, value in MOCK_POOL_DATA[network_key].items():
            if key.lower() == pool_lower:
                return value
    return None


def get_mock_token_data(network: str, token_address: str) -> Optional[Dict[str, Any]]:
    """Get mock token data for a given network and token address."""
    network_key = network.lower() if network else "eth"
    if network_key in MOCK_TOKEN_DATA:
        # Try exact match first
        if token_address in MOCK_TOKEN_DATA[network_key]:
            return MOCK_TOKEN_DATA[network_key][token_address]
        # Try case-insensitive match
        token_lower = token_address.lower()
        for key, value in MOCK_TOKEN_DATA[network_key].items():
            if key.lower() == token_lower:
                return value
    return None


def get_mock_token_price(network: str, token_address: str) -> Optional[Dict[str, Any]]:
    """Get mock token price for a given network and token address."""
    network_key = network.lower() if network else "eth"
    if network_key in MOCK_TOKEN_PRICES:
        if token_address in MOCK_TOKEN_PRICES[network_key]:
            return MOCK_TOKEN_PRICES[network_key][token_address]
        # Try case-insensitive match
        token_lower = token_address.lower()
        for key, value in MOCK_TOKEN_PRICES[network_key].items():
            if key.lower() == token_lower:
                return value
    return None


def get_mock_trending_pools(network: Optional[str] = None) -> Dict[str, Any]:
    """Get mock trending tokens data."""
    network_key = network.lower() if network else "all"
    if network_key in MOCK_TRENDING_TOKENS:
        return {"data": MOCK_TRENDING_TOKENS[network_key]}
    # Default to all networks
    return {"data": MOCK_TRENDING_TOKENS["all"]}


def get_mock_token_top_pools(network: str, token_address: str) -> Optional[Dict[str, Any]]:
    """Get mock top pools for a token."""
    token_data = get_mock_token_data(network, token_address)
    if token_data and "included" in token_data:
        return {"data": token_data["included"]}
    return {"data": []}

