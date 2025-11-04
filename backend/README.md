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

### Running the Server

#### Option 1: Using Makefile (Recommended - from project root)
```bash
# From project root
make dev-backend

# Or run both frontend and backend together
make dev
```

#### Option 2: Using uv (Recommended)
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Option 3: Activate venv and run
```bash
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Option 4: Direct Python execution
```bash
uv run python main.py
```

### API Documentation

Once the server is running, visit:
- API Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

### Environment Variables

Create a `.env` file in the backend directory:
```bash
# Example .env
API_KEY=your_api_key_here
HEDERA_NETWORK=testnet
```

### Development

- The server runs on `http://localhost:8000` by default
- CORS is configured to allow requests from `http://localhost:3000` (frontend)
- Hot reload is enabled with `--reload` flag

## Project Structure

```
backend/
├── main.py           # FastAPI application entry point
├── pyproject.toml    # Project dependencies and metadata
├── uv.lock          # Locked dependencies
└── .venv/           # Virtual environment (gitignored)
```

