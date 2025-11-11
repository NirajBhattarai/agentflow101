# Quick Start Guide

## Local Development (All Agents)

### Option 1: Using the Dev Script (Recommended)

```bash
cd backend
chmod +x dev-start.sh
./dev-start.sh
```

This will start all services with colored output and log files.

### Option 2: Using Makefile

```bash
# From project root
make dev-all-agents
```

### Option 3: Manual Start

```bash
cd backend

# Terminal 1: Main Backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Orchestrator
uv run -m agents.orchestrator.orchestrator

# Terminal 3: Balance Agent
uv run -m agents.balance

# Terminal 4: Liquidity Agent
uv run -m agents.liquidity

# Terminal 5: Bridge Agent
uv run -m agents.bridge

# Terminal 6: Swap Agent
uv run -m agents.swap
```

## Environment Setup

1. Copy environment template:
```bash
cd backend
# Create .env file with your API keys
```

2. Required environment variables:
```bash
GOOGLE_API_KEY=your_key_here
HEDERA_NETWORK=testnet
```

3. Optional ports (defaults work fine):
```bash
ORCHESTRATOR_PORT=9000
BALANCE_PORT=9997
LIQUIDITY_PORT=9998
BRIDGE_PORT=9996
SWAP_PORT=9995
```

## Verify Services

Once started, check:
- Main Backend: http://localhost:8000/docs
- Orchestrator: http://localhost:9000
- Balance Agent: http://localhost:9997
- Liquidity Agent: http://localhost:9998
- Bridge Agent: http://localhost:9996
- Swap Agent: http://localhost:9995


