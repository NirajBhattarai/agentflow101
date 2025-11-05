## Balance Agent (A2A JSON-RPC)

### Description

The Balance Agent retrieves account balance information from multiple blockchain chains including:
- **Polygon** (QuickSwap)
- **Hedera** (SaucerSwap, HeliSwap, Silk Suite)

### Run the agent server

```bash
cd backend/agents/balance
uv run .
```

Or use the Makefile:

```bash
make dev-balance
```

Server starts at `http://0.0.0.0:9997/`.

### Send a non-streaming request (message/send)

```bash
curl --location 'http://0.0.0.0:9997/' \
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
          { "kind": "text", "text": "Get HBAR balance for account 0.0.123456 on Hedera" }
        ]
      }
    }
  }'
```

### Send a streaming request (message/stream)

```bash
curl --location 'http://0.0.0.0:9997/' \
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
          { "kind": "text", "text": "Get all token balances for account 0x1234... on Polygon" }
        ]
      }
    }
  }'
```

### Example Queries

- "Get HBAR balance for account 0.0.123456 on Hedera"
- "Check USDC balance for address 0x1234... on Polygon"
- "Get all token balances for an account across all chains"
- "Check balance for address 0xabcd... on Polygon"

### Agent Tools

The agent has access to the following tools:

1. **get_balance_polygon** - Get account balance from Polygon chain
2. **get_balance_hedera** - Get account balance from Hedera chain
3. **get_balance_all_chains** - Get account balance from all supported chains

Each tool returns information about:
- Native token balance (MATIC for Polygon, HBAR for Hedera)
- Token balances (if token address/symbol provided)
- Balance in human-readable format
- Raw balance values
- Token decimals
- USD value estimates

### Response Format

#### Single Chain Response

```json
{
  "type": "balance",
  "chain": "polygon",
  "account_address": "0x1234...",
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

#### All Chains Response

```json
{
  "type": "balance_summary",
  "account_address": "0x1234...",
  "token_address": "USDC",
  "chains": {
    "polygon": { ... },
    "hedera": { ... }
  },
  "total_usd_value": "$2,251.00"
}
```

### Implementation Notes

The current implementation uses mock data. To integrate with real blockchain RPC calls, replace the mock implementations in the tool files with actual API calls to:

- **Polygon**: Web3.py or ethers.js for EVM-compatible chains
- **Hedera**: Hedera SDK for Hedera-specific accounts

### Testing

Run tests using:

```bash
# All balance tests
make test-balance

# Specific chain tests
make test-balance-polygon
make test-balance-hedera

# All chains aggregation tests
make test-balance-all-chains
```

