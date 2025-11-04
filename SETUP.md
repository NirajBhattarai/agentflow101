# AgentFlow 101 - Setup Guide

## Project Structure

```
agentflow101/
├── frontend/          # Next.js frontend application
├── backend/           # Python FastAPI backend with uv
└── README.md          # Project documentation
```

## Prerequisites

### Frontend
- Node.js 18+ and npm
- Or use nvm to manage Node versions

### Backend
- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Quick Start

### Using Makefile (Recommended)

1. Install all dependencies:
```bash
make install
```

2. Run both frontend and backend:
```bash
make dev
```

This will start:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup

#### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies (uv will create virtual environment automatically):
```bash
uv sync
```

3. Run the server:
```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

#### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at: http://localhost:3000

## Development

- Backend runs on port `8000`
- Frontend runs on port `3000`
- CORS is configured to allow frontend to communicate with backend
- Both servers support hot reload during development

## Environment Variables

### Backend
Create `backend/.env`:
```env
HEDERA_NETWORK=testnet
HEDERA_ACCOUNT_ID=your_account_id
HEDERA_PRIVATE_KEY=your_private_key
```

### Frontend
Create `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running Both Services

### Option 1: Using Makefile (Recommended)
```bash
make dev
```
This runs both services in parallel.

### Option 2: Manual - Terminal 1 - Backend:
```bash
cd backend
uv run uvicorn main:app --reload
```

### Option 2: Manual - Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

### Option 3: Using Makefile - Separate Terminals
Terminal 1:
```bash
make dev-backend
```

Terminal 2:
```bash
make dev-frontend
```

## Useful Commands

### Using Makefile
- `make help` - Show all available commands
- `make install` - Install all dependencies
- `make dev` - Run both frontend and backend
- `make dev-frontend` - Run only frontend
- `make dev-backend` - Run only backend
- `make build-frontend` - Build frontend for production
- `make clean` - Clean all build artifacts

### Backend (Manual)
- `uv sync` - Install/update dependencies
- `uv add <package>` - Add a new dependency
- `uv run <command>` - Run command in virtual environment
- `uv run python main.py` - Run backend directly
- `make install-backend` - Install backend dependencies
- `make dev-backend` - Run backend development server

### Frontend (Manual)
- `npm install` - Install dependencies
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `make install-frontend` - Install frontend dependencies
- `make dev-frontend` - Run frontend development server

## Troubleshooting

### Backend Issues
- If virtual environment is missing: `uv sync`
- If dependencies are outdated: `uv sync --upgrade`
- Check Python version: `python --version` (needs 3.11+)

### Frontend Issues
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear Next.js cache: `rm -rf .next`

## Project Status

This is the initial setup for the AgentFlow 101 project - a Cross-Chain DeFi Aggregator Platform with AI Agents for the Hedera Hello Future: Ascension Hackathon 2025.

