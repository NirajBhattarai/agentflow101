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

## Architecture

The agent uses `ParallelAgent` with two sub-agents:

1. **HederaLiquidityAgent**: Fetches liquidity from Hedera (SaucerSwap)
2. **PolygonLiquidityAgent**: Fetches liquidity from Polygon

Both sub-agents run concurrently, and results are combined into a unified response.

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

## See Also

- [Parallel Agents Guide](../swap/PARALLEL_AGENTS_GUIDE.md)
- [Google ADK Parallel Agents Documentation](https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/)

