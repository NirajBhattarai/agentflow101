.PHONY: help install-frontend install-backend install dev-frontend dev-backend dev build-frontend build-backend test test-liquidity test-liquidity-ethereum test-liquidity-bsc test-liquidity-polygon test-liquidity-hedera test-liquidity-all-chains clean dev-travily dev-liquidity

# Default target
help:
	@echo "AgentFlow 101 - Makefile Commands"
	@echo ""
	@echo "Installation:"
	@echo "  make install              - Install all dependencies (frontend + backend)"
	@echo "  make install-frontend     - Install frontend dependencies"
	@echo "  make install-backend     - Install backend dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev                 - Run both frontend and backend in development mode"
	@echo "  make dev-frontend        - Run frontend development server"
	@echo "  make dev-backend         - Run backend development server"
	@echo ""
	@echo "Agents:"
	@echo "  make dev-travily         - Run Travily agent server (port 9999)"
	@echo "  make dev-liquidity       - Run Liquidity agent server (port 9998)"
	@echo ""
	@echo "Build:"
	@echo "  make build-frontend      - Build frontend for production"
	@echo "  make build-backend       - Build backend (check dependencies)"
	@echo ""
	@echo "Testing:"
	@echo "  make test                - Run all tests"
	@echo "  make test-liquidity      - Run all liquidity agent tests"
	@echo "  make test-liquidity-ethereum - Run Ethereum liquidity tests"
	@echo "  make test-liquidity-bsc  - Run BSC liquidity tests"
	@echo "  make test-liquidity-polygon - Run Polygon liquidity tests"
	@echo "  make test-liquidity-hedera - Run Hedera liquidity tests"
	@echo "  make test-liquidity-all-chains - Run all chains aggregation tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean               - Clean build artifacts and dependencies"

# Installation
install: install-frontend install-backend

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && uv sync

install-backend-test:
	@echo "Installing backend dependencies with test extras..."
	cd backend && uv sync --extra test

# Development servers
dev:
	@echo "Starting both frontend and backend..."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@make -j2 dev-frontend dev-backend

dev-frontend:
	@echo "Starting frontend development server..."
	cd frontend && npm run dev

dev-backend:
	@echo "Starting backend development server..."
	cd backend && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Agent servers
dev-travily:
	@echo "Starting Travily agent server..."
	@echo "Travily Agent: http://localhost:9999"
	cd travily && uv run .

dev-liquidity:
	@echo "Starting Liquidity agent server..."
	@echo "Liquidity Agent: http://localhost:9998"
	cd backend && uv run -m agents.liquidity

# Production builds
build-frontend:
	@echo "Building frontend for production..."
	cd frontend && npm run build

build-backend:
	@echo "Checking backend dependencies..."
	cd backend && uv sync --frozen

# Testing
test:
	@echo "Running all tests..."
	cd backend && uv run pytest

test-liquidity:
	@echo "Running liquidity agent tests..."
	cd backend && PYTHONPATH=. uv run pytest agents/liquidity/__test__ -v

test-liquidity-ethereum:
	@echo "Running Ethereum liquidity tests..."
	cd backend && PYTHONPATH=. uv run pytest agents/liquidity/__test__/test_ethereum.py -v

test-liquidity-bsc:
	@echo "Running BSC liquidity tests..."
	cd backend && PYTHONPATH=. uv run pytest agents/liquidity/__test__/test_bsc.py -v

test-liquidity-polygon:
	@echo "Running Polygon liquidity tests..."
	cd backend && PYTHONPATH=. uv run pytest agents/liquidity/__test__/test_polygon.py -v

test-liquidity-hedera:
	@echo "Running Hedera liquidity tests..."
	cd backend && PYTHONPATH=. uv run pytest agents/liquidity/__test__/test_hedera.py -v

test-liquidity-all-chains:
	@echo "Running all chains liquidity tests..."
	cd backend && PYTHONPATH=. uv run pytest agents/liquidity/__test__/test_all_chains.py -v

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	rm -rf frontend/.next
	rm -rf frontend/node_modules
	rm -rf frontend/package-lock.json
	rm -rf backend/.venv
	rm -rf backend/__pycache__
	rm -rf backend/**/__pycache__
	@echo "Clean complete. Run 'make install' to reinstall dependencies."

