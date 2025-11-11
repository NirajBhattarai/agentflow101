# Swap Agent

A blockchain token swap agent that handles token swaps on multiple blockchain chains (Polygon and Hedera) using Google ADK and A2A Protocol.

## Overview

The Swap Agent provides comprehensive swap functionality including:
- **Token swaps** on Polygon and Hedera chains
- **Multiple DEX support** (SaucerSwap, HeliSwap, QuickSwap, Uniswap)
- **Balance checking** before swap execution
- **Slippage tolerance** configuration
- **Direct swap execution** (TEMPORARY: no quotes, executes immediately)

## Architecture

The Swap Agent follows a clean, modular architecture with clear separation of concerns:

```
swap/
├── __init__.py              # Package initialization
├── __main__.py              # Server entry point
├── agent.py                 # Agent definition (SwapAgent class)
├── executor.py              # A2A Protocol executor (SwapExecutor class)
├── README.md                # This file
│
├── core/                    # Core domain logic
│   ├── __init__.py
│   ├── constants.py        # Configuration constants and defaults
│   ├── exceptions.py        # Custom domain exceptions
│   ├── agent_instruction.py # LLM instruction prompt
│   ├── response_validator.py # Response validation utilities
│   └── models/              # Domain models (Pydantic)
│       ├── __init__.py
│       └── swap.py          # SwapTransaction, SwapOption, SwapBalanceCheck, StructuredSwap
│
├── services/                # Application services
│   ├── __init__.py
│   ├── query_parser.py     # Query parsing and parameter extraction
│   ├── swap_executor_service.py # Swap execution logic
│   ├── response_builder.py # Response construction
│   └── response_validator.py # Response validation and error handling
│
├── tools/                   # Blockchain interaction adapters
│   ├── __init__.py
│   ├── constants.py        # Token addresses, DEX configs, chain configs
│   ├── extract_swap_params.py # Parameter extraction utilities
│   ├── hedera.py           # Hedera chain swap execution
│   └── polygon.py          # Polygon chain swap execution
│
└── __test__/               # Test suite (to be added)
    └── ...
```

## Architecture Layers

### 1. **Core Layer** (`core/`)
Contains fundamental building blocks:
- **`constants.py`**: All configuration values, defaults, error messages
- **`exceptions.py`**: Custom domain exceptions (`SwapAgentError`, `InvalidSwapParametersError`, `ChainNotSupportedError`, etc.)
- **`agent_instruction.py`**: LLM instruction prompt for parameter extraction
- **`models/swap.py`**: Pydantic domain models (`SwapTransaction`, `SwapOption`, `SwapBalanceCheck`, `StructuredSwap`)
- **`response_validator.py`**: Response validation and serialization utilities

### 2. **Services Layer** (`services/`)
Contains application service utilities:
- **`query_parser.py`**: Extracts swap parameters from user queries (chain, tokens, amount, slippage)
- **`swap_executor_service.py`**: Executes swaps, fetches balances, creates transactions
- **`response_builder.py`**: Constructs swap responses and error responses
- **`response_validator.py`**: Validates response content, handles errors, and logs responses

### 3. **Agent Layer** (`agent.py`)
Defines the main agent:
- **`SwapAgent`**: Google ADK agent that handles swap queries
  - Builds and configures the LLM agent
  - Uses LLM with tools to extract swap parameters
  - Falls back to regex parsing if LLM fails
  - Executes swaps and returns structured JSON responses

### 4. **Executor Layer** (`executor.py`)
Thin adapter layer for A2A Protocol:
- **`SwapExecutor`**: Implements `AgentExecutor` interface
  - Receives requests from orchestrator
  - Delegates to agent and services
  - Handles A2A Protocol-specific concerns only
  - Minimal business logic (thin layer pattern)

### 5. **Tools Layer** (`tools/`)
Blockchain interaction layer:
- **`hedera.py`**: Executes swaps on Hedera chain
- **`polygon.py`**: Executes swaps on Polygon chain
- **`constants.py`**: Token addresses, DEX configurations, RPC URLs
- **`extract_swap_params.py`**: Parameter extraction utilities

## Design Principles

### Clean Code Architecture
- **Separation of Concerns**: Each module has a single, well-defined responsibility
- **Small Methods**: All methods are ≤ 8 lines for maintainability
- **Dependency Injection**: Services are imported and used, not tightly coupled
- **Constants Extraction**: All magic strings and configuration moved to constants

## Supported Chains and Tokens

### Polygon
- **DEXes**: QuickSwap, Uniswap V3
- **Tokens**: MATIC, USDC, USDT, WMATIC, DAI, ETH, WBTC, WETH, LINK, AAVE, UNI, CRV

### Hedera
- **DEXes**: SaucerSwap, HeliSwap
- **Tokens**: HBAR, USDC, USDT, WHBAR, ETH, WETH, BTC, SAUCE, LINK, AVAX

## Usage

### Running the Agent Server

```bash
# From backend directory
cd backend/agents/swap
uv run .

# Or use Makefile
make dev-swap
```

Server starts at `http://0.0.0.0:9995/`

### Example Queries

- "Swap 0.01 HBAR to USDC on Hedera"
- "Swap 100 USDC to HBAR on Hedera"
- "Swap 50 MATIC to USDC on Polygon"
- "Swap 0.1 HBAR to USDC on Hedera for account 0.0.123456"

### Response Format

```json
{
  "type": "swap",
  "chain": "hedera",
  "token_in_symbol": "HBAR",
  "token_out_symbol": "USDC",
  "amount_in": "0.01",
  "account_address": "0.0.123456",
  "balance_check": {
    "account_address": "0.0.123456",
    "token_symbol": "HBAR",
    "balance": "100.00",
    "balance_sufficient": true,
    "required_amount": "0.01"
  },
  "transaction": {
    "chain": "hedera",
    "token_in_symbol": "HBAR",
    "token_in_address": "0x...",
    "token_out_symbol": "USDC",
    "token_out_address": "0x...",
    "amount_in": "0.01",
    "amount_out": "0.95",
    "amount_out_min": "0.94",
    "swap_fee": "$0.00",
    "swap_fee_percent": 0.3,
    "estimated_time": "~30 seconds",
    "dex_name": "SaucerSwap",
    "pool_address": "0x...",
    "slippage_tolerance": 0.5,
    "transaction_hash": "0x...",
    "status": "pending",
    "price_impact": "0.1%"
  },
  "requires_confirmation": false,
  "confirmation_threshold": 100.0,
  "amount_exceeds_threshold": false
}
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
SWAP_PORT=9995  # Default
```

## Code Quality

- ✅ Clean separation of concerns
- ✅ Small, focused methods
- ✅ Comprehensive error handling
- ✅ Type hints throughout
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

2. Token will automatically be available for swaps

### Adding a New Chain

1. Create new tool file in `tools/` (e.g., `ethereum.py`)
2. Add chain constants to `tools/constants.py`
3. Update `services/swap_executor_service.py` to handle new chain
4. Update `services/query_parser.py` for chain detection
5. Add tests

## Integration

The Swap Agent integrates with:
- **Orchestrator Agent**: Called via A2A Protocol for swap requests
- **Balance Agent**: Used to check balances before swap execution
- **Frontend**: Displays swap information and transaction status

## License

Part of AgentFlow 101 - Hedera Hello Future: Ascension Hackathon 2025

