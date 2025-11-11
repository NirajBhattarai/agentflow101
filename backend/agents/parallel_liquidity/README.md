# Parallel Liquidity Agent

An independent agent that fetches liquidity information from multiple blockchain chains **in parallel** using Google ADK's `ParallelAgent`.

## Overview

This agent uses `ParallelAgent` to simultaneously query liquidity from:
- **Hedera** (SaucerSwap DEX)
- **Polygon** (QuickSwap and other DEXes)

When given a token pair like "ETH/USDT", it fetches liquidity from both chains concurrently, significantly reducing response time.

## Features

- ✅ **Parallel Execution**: Fetches from multiple chains simultaneously
- ✅ **Token Pair Support**: Handles pairs like ETH/USDT, HBAR/USDC, etc.
- ✅ **Independent Agent**: Completely separate from the regular liquidity agent
- ✅ **Fallback Support**: Falls back to sequential execution if ParallelAgent is unavailable
- ✅ **A2A Protocol**: Exposes A2A Protocol endpoint for orchestrator integration
- ✅ **Clean Architecture**: Modular structure with clear separation of concerns

## Architecture

The Parallel Liquidity Agent follows a clean, modular architecture with clear separation of concerns:

```
parallel_liquidity/
├── __init__.py              # Package initialization
├── __main__.py              # Server entry point
├── agent.py                 # Agent definition (ParallelLiquidityAgent class)
├── executor.py              # A2A Protocol executor (thin adapter layer)
├── README.md                # This file
│
├── core/                    # Core domain logic
│   ├── __init__.py
│   ├── constants.py        # Configuration constants and defaults
│   ├── exceptions.py        # Custom domain exceptions
│   ├── response_validator.py # Response validation utilities
│   └── models/              # Domain models (Pydantic)
│       ├── __init__.py
│       └── liquidity.py     # LiquidityPair, StructuredParallelLiquidity models
│
├── services/                # Application services
│   ├── __init__.py
│   ├── query_parser.py     # Token pair extraction from queries
│   ├── result_combiner.py  # Result combination logic
│   └── response_validator.py # Response validation and error handling
│
├── agents/                  # Sub-agents for parallel execution
│   ├── __init__.py
│   ├── hedera_liquidity_agent.py  # Hedera liquidity sub-agent
│   └── polygon_liquidity_agent.py # Polygon liquidity sub-agent
│
└── __test__/               # Test suite
    ├── conftest.py         # Test fixtures
    ├── test_token_pair_extraction.py # Token pair extraction tests
    ├── test_result_combination.py    # Result combination tests
    ├── test_sub_agents.py            # Sub-agents tests
    └── test_integration.py           # Integration tests
```

## Architecture Layers

### 1. **Core Layer** (`core/`)
Contains fundamental building blocks:
- **`constants.py`**: All configuration values, defaults, error messages
- **`exceptions.py`**: Custom domain exceptions (`ParallelLiquidityAgentError`, `TokenPairExtractionError`, `ResultCombinationError`, `ValidationError`)
- **`models/liquidity.py`**: Pydantic domain models (`LiquidityPair`, `StructuredParallelLiquidity`)
- **`response_validator.py`**: Response validation and serialization utilities

### 2. **Services Layer** (`services/`)
Contains application service utilities:
- **`query_parser.py`**: Extracts token pairs from user queries (e.g., "ETH/USDT", "HBAR/USDC")
- **`result_combiner.py`**: Combines liquidity results from multiple chains into unified response
- **`response_validator.py`**: Validates response content, handles errors, and logs responses

### 3. **Agent Layer** (`agent.py`)
Defines the main agent:
- **`ParallelLiquidityAgent`**: Google ADK agent that handles parallel liquidity queries
  - Builds and configures the ParallelAgent with sub-agents
  - Falls back to sequential execution if ParallelAgent unavailable
  - Processes queries and invokes appropriate sub-agents
  - Returns structured JSON responses

### 4. **Executor Layer** (`executor.py`)
Thin adapter layer for A2A Protocol:
- **`ParallelLiquidityExecutor`**: Implements `AgentExecutor` interface
  - Receives requests from orchestrator
  - Delegates to agent and services
  - Handles A2A Protocol-specific concerns only
  - Minimal business logic (thin layer pattern)

### 5. **Sub-Agents Layer** (`agents/`)
Independent sub-agents for parallel execution:
- **`hedera_liquidity_agent.py`**: Fetches liquidity from Hedera chain (SaucerSwap)
- **`polygon_liquidity_agent.py`**: Fetches liquidity from Polygon chain

## Usage

### Running the Agent

```bash
# From backend directory
uv run -m agents.parallel_liquidity

# Or with custom port
PARALLEL_LIQUIDITY_PORT=9994 uv run -m agents.parallel_liquidity
```

### Example Queries

```
Get liquidity for ETH/USDT
Find liquidity pools for HBAR/USDC on Hedera and Polygon
Get liquidity for USDC/USDT across all chains
Show me liquidity for MATIC/USDC
```

### Response Format

```json
{
  "type": "parallel_liquidity",
  "token_pair": "ETH/USDT",
  "chains": {
    "hedera": {
      "pairs": [...],
      "total_pools": 2
    },
    "polygon": {
      "pairs": [...],
      "total_pools": 1
    }
  },
  "hedera_pairs": [...],
  "polygon_pairs": [...],
  "all_pairs": [...]
}
```

## Configuration

Set environment variables:

```bash
PARALLEL_LIQUIDITY_PORT=9994  # Default port
GOOGLE_API_KEY=your_key_here  # Required for ADK
GEMINI_MODEL=gemini-2.5-flash # Optional, defaults to gemini-2.5-flash
```

## Performance

**Sequential Execution:**
- Hedera query: ~500ms
- Polygon query: ~500ms
- **Total: ~1000ms**

**Parallel Execution:**
- Both queries simultaneously: ~500ms
- **Total: ~500ms** (2x faster!)

## Integration

The agent exposes an A2A Protocol endpoint that can be called by:
- The orchestrator agent
- Other agents via `send_message_to_a2a_agent`
- Direct HTTP requests

## Dependencies

- Uses liquidity tools from `agents.liquidity.tools`
- Requires Google ADK with ParallelAgent support (v0.1.0+)
- Falls back to sequential execution if ParallelAgent unavailable

## Testing

Run tests using Makefile:

```bash
make test-parallel-liquidity              # Run all tests
make test-parallel-liquidity-unit         # Run unit tests only
make test-parallel-liquidity-integration  # Run integration tests only
```

## See Also

- [Parallel Agents Guide](../swap/PARALLEL_AGENTS_GUIDE.md)
- [Google ADK Parallel Agents Documentation](https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/)
