# AgentFlow Backend

Backend API for AgentFlow - Cross-Chain DeFi Aggregator Platform with AI Agents.

## Setup

### Prerequisites
- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

1. Install dependencies and create virtual environment:
```bash
cd backend
uv sync
```

This will automatically create a `.venv` virtual environment and install all dependencies.

### Running All Services (Development)

#### Option 1: Dev Script (Recommended - All Agents)
```bash
cd backend
./dev-start.sh
```
Starts all agents with colored output and log files in `logs/` directory.

#### Option 2: Using Makefile (from project root)
```bash
# Run all agents
make dev-all-agents

# Or run just main backend
make dev-backend

# Or run both frontend and backend together
make dev
```

#### Option 3: Production Start Script
```bash
cd backend
./start.sh
```
Starts all services in background (for Railway/production).

### Running Individual Services

#### Main Backend Only
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Individual Agents
```bash
# Orchestrator
uv run -m agents.orchestrator.orchestrator

# Balance Agent
uv run -m agents.balance

# Liquidity Agent
uv run -m agents.liquidity

# Bridge Agent
uv run -m agents.bridge

# Swap Agent
uv run -m agents.swap

# Parallel Liquidity Agent
uv run -m agents.parallel_liquidity
```

### API Documentation

Once the server is running, visit:
- API Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

### Environment Variables

Create a `.env` file in the backend directory:
```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here
HEDERA_NETWORK=testnet

# Optional (defaults shown)
ORCHESTRATOR_PORT=9000
BALANCE_PORT=9997
LIQUIDITY_PORT=9998
BRIDGE_PORT=9996
SWAP_PORT=9995
PARALLEL_LIQUIDITY_PORT=9994
FRONTEND_URL=http://localhost:3000
```

Get your Google API key from: https://aistudio.google.com/app/apikey

### Development

- The server runs on `http://localhost:8000` by default
- CORS is configured to allow requests from `http://localhost:3000` (frontend)
- Hot reload is enabled with `--reload` flag

## Deployment

### Railway Deployment

See [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) for complete Railway setup guide.

Quick steps:
1. Push code to GitHub
2. Connect Railway to your repo
3. Set `GOOGLE_API_KEY` and other env vars in Railway dashboard
4. Deploy!

The `Dockerfile` and `start.sh` are configured for Railway deployment.

### Service Ports

- Main Backend: 8000
- Orchestrator Agent: 9000
- Balance Agent: 9997
- Liquidity Agent: 9998
- Bridge Agent: 9996
- Swap Agent: 9995

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── pyproject.toml       # Project dependencies and metadata
├── uv.lock             # Locked dependencies
├── Dockerfile          # Docker configuration for Railway
├── start.sh            # Production start script (all agents)
├── dev-start.sh        # Development start script (all agents)
├── railway.json        # Railway configuration
├── railway.toml        # Railway configuration (alternative)
├── RAILWAY_DEPLOYMENT.md  # Railway deployment guide
├── QUICK_START.md      # Quick start guide
├── agents/             # Agent modules
│   ├── orchestrator/   # Orchestrator agent
│   ├── balance/        # Balance agent
│   ├── liquidity/      # Liquidity agent
│   ├── bridge/         # Bridge agent
│   └── swap/           # Swap agent
└── .venv/              # Virtual environment (gitignored)
```

