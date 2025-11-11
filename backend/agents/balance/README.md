# Balance Agent

A blockchain balance query agent that retrieves account balance information from multiple blockchain chains (Polygon and Hedera) using Google ADK and A2A Protocol.

## Overview

The Balance Agent provides comprehensive balance information including:
- **Native token balances** (MATIC for Polygon, HBAR for Hedera)
- **Token balances** for all supported tokens on each chain
- **Multi-chain support** - Query single chain or aggregate across all chains
- **Comprehensive token coverage** - 11 tokens on Polygon, 16 tokens on Hedera

## Architecture

The Balance Agent follows a clean, modular architecture with clear separation of concerns:

```
balance/
├── __init__.py              # Package initialization
├── __main__.py              # Server entry point
├── agent.py                 # Agent definition (BalanceAgent class)
├── executor.py              # A2A Protocol executor (thin adapter layer)
├── README.md                # This file
├── IMPROVEMENTS.md          # Architecture improvement proposals
│
├── core/                    # Core domain logic
│   ├── __init__.py
│   ├── constants.py        # Configuration constants and defaults
│   ├── exceptions.py        # Custom domain exceptions
│   ├── response_validator.py # Response validation utilities
│   └── models/              # Domain models (Pydantic)
│       ├── __init__.py
│       └── balance.py       # TokenBalance, StructuredBalance models
│
├── services/                # Application services
│   ├── __init__.py
│   ├── query_parser.py     # Query parsing and chain detection
│   ├── response_builder.py # Response construction for different chains
│   └── response_validator.py # Response validation and error handling
│
├── tools/                   # Blockchain interaction adapters
│   ├── __init__.py
│   ├── constants.py        # Token addresses and chain configurations
│   ├── polygon.py          # Polygon chain balance fetching
│   ├── hedera.py           # Hedera chain balance fetching
│   ├── all_chains.py       # Multi-chain aggregation
│   ├── log_message.py      # Logging utility
│   └── abi/
│       └── erc20.py        # ERC-20 ABI definitions
│
└── __test__/               # Test suite
    ├── conftest.py         # Test fixtures
    ├── test_polygon.py     # Polygon-specific tests
    ├── test_hedera.py      # Hedera-specific tests
    ├── test_all_chains.py  # Multi-chain tests
    └── test_balance_executor.py # Executor tests
```

## Architecture Layers

### 1. **Core Layer** (`core/`)
Contains fundamental building blocks:
- **`constants.py`**: All configuration values, defaults, error messages, and agent instructions
- **`exceptions.py`**: Custom domain exceptions (`BalanceAgentError`, `InvalidAddressError`, `ChainNotSupportedError`, etc.)
- **`models/balance.py`**: Pydantic domain models (`TokenBalance`, `StructuredBalance`)
- **`response_validator.py`**: Response validation and serialization utilities

### 2. **Services Layer** (`services/`)
Contains application service utilities:
- **`query_parser.py`**: Extracts account addresses and detects chains from user queries
- **`response_builder.py`**: Constructs balance responses for different chains
- **`response_validator.py`**: Validates response content, handles errors, and logs responses

### 3. **Agent Layer** (`agent.py`)
Defines the main agent:
- **`BalanceAgent`**: Google ADK agent that handles balance queries
  - Builds and configures the LLM agent
  - Processes queries and invokes appropriate tools
  - Returns structured JSON responses

### 4. **Executor Layer** (`executor.py`)
Thin adapter layer for A2A Protocol:
- **`BalanceExecutor`**: Implements `AgentExecutor` interface
  - Receives requests from orchestrator
  - Delegates to agent and services
  - Handles A2A Protocol-specific concerns only
  - Minimal business logic (thin layer pattern)

### 5. **Tools Layer** (`tools/`)
Blockchain interaction layer:
- **`polygon.py`**: Fetches balances from Polygon chain (Web3)
- **`hedera.py`**: Fetches balances from Hedera chain (Mirror Node API)
- **`all_chains.py`**: Aggregates balances across chains
- **`constants.py`**: Token addresses and chain-specific configurations

## Design Principles

### Clean Code Architecture
- **Separation of Concerns**: Each module has a single, well-defined responsibility
- **Small Methods**: All methods are ≤ 8 lines for maintainability
- **Dependency Injection**: Services are imported and used, not tightly coupled
- **Constants Extraction**: All magic strings and configuration moved to constants

### Module Responsibilities

| Module | Responsibility | Dependencies |
|--------|---------------|--------------|
| `core/constants.py` | Configuration values | None |
| `core/response_validator.py` | Data models & validation | `core/constants.py` |
| `services/query_parser.py` | Query parsing | `core/constants.py` |
| `services/response_builder.py` | Response building | `tools/`, `core/constants.py` |
| `agent.py` | Agent definition | `core/`, `services/`, `tools/` |
| `executor.py` | A2A Protocol execution | `agent.py`, `core/` |
| `tools/*.py` | Blockchain interactions | `core/constants.py` |

## Supported Tokens

### Polygon (11 tokens)
- MATIC (native), WMATIC, POL, USDC, WETH, DAI, AAVE, LINK, QUICK, SAND, USDT

### Hedera (16 tokens)
- HBAR (native), SAUCE, USDC, JAM, DOV, HBARX, SHIBR, SKUX, TNG, HTC, USDT, WHBAR, ETH, WETH, BTC, LINK, AVAX

## Usage

### Running the Agent Server

```bash
# From backend directory
cd backend/agents/balance
uv run .

# Or use Makefile
make dev-balance
```

Server starts at `http://0.0.0.0:9997/`

### Example Queries

- "Get HBAR balance for account 0.0.123456 on Hedera"
- "Check USDC balance for address 0x1234... on Polygon"
- "Get all token balances for account 0xabcd... on all chains"
- "Check balance for address 0x1234... on Polygon"

### Response Format

```json
{
  "type": "balance",
  "chain": "polygon | hedera | all",
  "account_address": "0x... or 0.0.123456",
  "balances": [
    {
      "token_type": "native",
      "token_symbol": "MATIC",
      "token_address": "0x0000...",
      "balance": "1.5",
      "balance_raw": "1500000000000000000",
      "decimals": 18
    },
    {
      "token_type": "token",
      "token_symbol": "USDC",
      "token_address": "0x2791...",
      "balance": "1000.0",
      "balance_raw": "1000000000",
      "decimals": 6
    }
  ],
  "total_usd_value": "$1,501.00"
}
```

## Testing

```bash
# All balance tests
make test-balance

# Specific chain tests
make test-balance-polygon
make test-balance-hedera

# All chains aggregation tests
make test-balance-all-chains
```

## Configuration

Set environment variables:

```bash
# API Keys
GOOGLE_API_KEY=your_key_here
# OR
GEMINI_API_KEY=your_key_here

# Model Configuration
GEMINI_MODEL=gemini-2.5-flash  # Default

# Network Configuration
POLYGON_RPC_URL=https://polygon-rpc.com  # Default
HEDERA_NETWORK=mainnet  # Default (or testnet)

# Server Configuration
BALANCE_PORT=9997  # Default
```

## Code Quality

- ✅ All methods ≤ 8 lines
- ✅ Clean separation of concerns
- ✅ Comprehensive test coverage
- ✅ Type hints throughout
- ✅ Error handling at all layers
- ✅ Constants extracted to dedicated files

## Development

### Adding a New Token

1. Add token to `tools/constants.py`:
   ```python
   POLYGON_TOKENS = {
       ...
       "NEW_TOKEN": "0x...",
   }
   ```

2. Token will automatically be included in balance queries

### Adding a New Chain

1. Create new tool file in `tools/` (e.g., `ethereum.py`)
2. Add chain constants to `tools/constants.py`
3. Update `services/response_builder.py` to handle new chain
4. Update `services/query_parser.py` for chain detection
5. Add tests in `__test__/`

## Integration

The Balance Agent integrates with:
- **Orchestrator Agent**: Called via A2A Protocol for balance queries
- **Frontend**: Displays balance information via `BalanceCard` component
- **Other Agents**: Can be called by Bridge/Swap agents for balance checks

## License

Part of AgentFlow 101 - Hedera Hello Future: Ascension Hackathon 2025
