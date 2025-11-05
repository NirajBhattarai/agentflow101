## Liquidity Agent (A2A JSON-RPC)

### Description

The Liquidity Agent retrieves liquidity information from multiple blockchain chains including:
- **Polygon** (QuickSwap)
- **Hedera** (SaucerSwap, HeliSwap, Silk Suite)

### Run the agent server

```bash
cd backend/agents/liquidity
uv run .
```

Server starts at `http://0.0.0.0:9998/`.

### Send a non-streaming request (message/send)

```bash
curl --location 'http://0.0.0.0:9998/' \
  --header 'Content-Type: application/json' \
  --data '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "message/send",
    "params": {
      "message": {
        "kind": "message",
        "message_id": "00000000-0000-0000-0000-000000000001",
        "role": "user",
        "parts": [
          { "kind": "text", "text": "Get liquidity for USDC token on Hedera" }
        ]
      }
    }
  }'
```

### Send a streaming request (message/stream)

```bash
curl --location 'http://0.0.0.0:9998/' \
  --header 'Content-Type: application/json' \
  --header 'Accept: text/event-stream' \
  --no-buffer \
  --data '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "message/stream",
    "params": {
      "message": {
        "kind": "message",
        "message_id": "00000000-0000-0000-0000-000000000002",
        "role": "user",
        "parts": [
          { "kind": "text", "text": "Get liquidity for HBAR on all chains" }
        ]
      }
    }
  }'
```

### Example Queries

- "Get liquidity for USDC token on Hedera"
- "Find all liquidity pools for HBAR on Hedera"
- "Compare liquidity across all chains for a token"
- "Get liquidity information from Polygon"

### Agent Tools

The agent has access to the following tools:

1. **get_liquidity_polygon** - Get liquidity from Polygon chain
2. **get_liquidity_hedera** - Get liquidity from Hedera chain
3. **get_liquidity_all_chains** - Get liquidity from all supported chains

Each tool returns information about:
- Pool addresses
- DEX names
- Token pairs
- Total Value Locked (TVL)
- 24-hour trading volume

### Implementation Notes

The current implementation uses mock data. To integrate with real DEX APIs, replace the mock implementations in `liquidity_executor.py` with actual API calls to:

- **Polygon**: QuickSwap API
- **Hedera**: SaucerSwap API, HeliSwap API, Silk Suite API

