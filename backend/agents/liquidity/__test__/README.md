# Liquidity Agent Tests

This directory contains unit tests for the liquidity agent tools. Each test file focuses on testing a specific chain's liquidity fetching functionality.

## Test Structure

- `test_polygon.py` - Tests for Polygon chain liquidity tools
- `test_hedera.py` - Tests for Hedera chain liquidity tools
- `test_all_chains.py` - Tests for all chains aggregation tool
- `conftest.py` - Pytest configuration and shared fixtures

## Prerequisites

1. Install test dependencies:
```bash
cd backend
uv sync --extra test
```

Or use the Makefile:
```bash
make install-backend-test
```

## Running Tests

### Run All Liquidity Tests
```bash
make test-liquidity
```

### Run Tests for Specific Chain

**Polygon:**
```bash
make test-liquidity-polygon
```

**Hedera:**
```bash
make test-liquidity-hedera
```

**All Chains Aggregation:**
```bash
make test-liquidity-all-chains
```

### Run Tests Directly with pytest

```bash
cd backend
uv run pytest agents/liquidity/__test__ -v
```

## RPC Configuration

Tests use RPC endpoints to fetch actual data from chains. You can configure custom RPC URLs via environment variables:

```bash
export POLYGON_RPC_URL="https://your-polygon-rpc-url"
export HEDERA_RPC_URL="https://your-hedera-rpc-url"
```

Default RPC URLs (public endpoints):
- Polygon: `https://polygon.llamarpc.com`
- Hedera: `https://mainnet.hashio.io/api`

## Test Coverage

Each test file includes:
- Token address lookup tests
- Pool address resolution tests
- RPC connection tests
- Contract existence verification
- Chain-specific validations (chain ID, block numbers, etc.)

## Notes

- Tests that require RPC connections may skip if the RPC endpoint is unavailable
- Some tests verify contract addresses exist on-chain
- Hedera uses a REST API instead of standard Web3 RPC, so tests are adapted accordingly

