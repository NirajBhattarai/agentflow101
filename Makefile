.PHONY: help install-frontend install-backend install-backend-test install-backend-dev install \
        dev-frontend dev-backend dev build-frontend build-backend test \
        test-liquidity test-liquidity-polygon test-liquidity-hedera \
        test-liquidity-all-chains test-balance test-balance-polygon test-balance-hedera \
        test-balance-all-chains test-swap test-swap-unit test-swap-integration \
        test-orchestrator test-orchestrator-unit test-orchestrator-integration \
        test-parallel-liquidity test-parallel-liquidity-unit test-parallel-liquidity-integration \
        test-pools test-liquidity-blockchain test-tokens test-tokens-constants test-tokens-address \
        test-balance-shared \
        clean dev-travily dev-liquidity dev-parallel-liquidity dev-balance dev-swap \
        dev-orchestrator dev-all-agents format format-backend format-frontend backend

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
	@echo "  make dev-parallel-liquidity - Run Parallel Liquidity agent server (port 9994)"
	@echo "  make dev-balance         - Run Balance agent server (port 9997)"
	@echo "  make dev-swap            - Run Swap agent server (port 9995)"
	@echo "  make dev-orchestrator    - Run Orchestrator agent server (port 9000)"
	@echo "  make dev-all-agents      - Run all agents (orchestrator, balance, liquidity, parallel-liquidity, swap)"
	@echo ""
	@echo "Build:"
	@echo "  make build-frontend      - Build frontend for production"
	@echo "  make build-backend       - Build backend (check dependencies)"
	@echo ""
	@echo "Testing:"
	@echo "  make test                - Run all tests"
	@echo "  make test-liquidity      - Run all liquidity agent tests"
	@echo "  make test-liquidity-polygon - Run Polygon liquidity tests"
	@echo "  make test-liquidity-hedera - Run Hedera liquidity tests"
	@echo "  make test-liquidity-all-chains - Run all chains aggregation tests"
	@echo "  make test-balance        - Run all balance agent tests"
	@echo "  make test-balance-polygon - Run Polygon balance tests"
	@echo "  make test-balance-hedera - Run Hedera balance tests"
	@echo "  make test-balance-all-chains - Run all chains balance aggregation tests"
	@echo "  make test-balance-integration - Run balance agent integration tests"
	@echo "  make test-swap - Run all swap agent tests"
	@echo "  make test-swap-unit - Run swap agent unit tests"
	@echo "  make test-swap-integration - Run swap agent integration tests"
	@echo "  make test-orchestrator - Run all orchestrator agent tests"
	@echo "  make test-orchestrator-unit - Run orchestrator agent unit tests"
	@echo "  make test-orchestrator-integration - Run orchestrator agent integration tests"
	@echo "  make test-parallel-liquidity - Run all parallel liquidity agent tests"
	@echo "  make test-parallel-liquidity-unit - Run parallel liquidity agent unit tests"
	@echo "  make test-parallel-liquidity-integration - Run parallel liquidity agent integration tests"
	@echo "  make test-pools - Run pools tests (Uniswap V3 pool address tests)"
	@echo "  make test-liquidity-blockchain - Run liquidity blockchain tests (liquidity and slot0)"
	@echo "  make test-tokens - Run all token tests"
	@echo "  make test-tokens-constants - Run token constants tests"
	@echo "  make test-tokens-address - Run token address function tests"
	@echo "  make test-balance-shared - Run shared balance library tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean               - Clean build artifacts and dependencies"
	@echo ""
	@echo "Formatting:"
	@echo "  make format-backend      - Auto-format and lint-fix backend (ruff)"
	@echo "  make format-frontend     - Auto-format frontend (prettier)"
	@echo "  make format              - Format all (backend + frontend)"

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

install-backend-dev:
	@echo "Installing backend dev dependencies (formatters, linters)..."
	cd backend && uv sync --extra dev

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

dev-balance:
	@echo "Starting Balance agent server..."
	@echo "Balance Agent: http://localhost:9997"
	cd backend && uv run -m agents.balance

dev-swap:
	@echo "Starting Swap agent server..."
	@echo "Swap Agent: http://localhost:9995"
	cd backend && uv run -m agents.swap

dev-parallel-liquidity:
	@echo "Starting Parallel Liquidity agent server..."
	@echo "Parallel Liquidity Agent: http://localhost:9994"
	cd backend && uv run -m agents.parallel_liquidity

dev-orchestrator:
	@echo "Starting Orchestrator agent server..."
	@echo "Orchestrator Agent: http://localhost:9000"
	# Ensure environment is loaded from backend/.env, then run from backend
	cd backend && set -a; [ -f .env ] && . .env; set +a; uv run -m agents.orchestrator.orchestrator

dev-all-agents:
	@echo "Starting all agent servers..."
	@echo "Orchestrator: http://localhost:9000"
	@echo "Balance Agent: http://localhost:9997"
	@echo "Liquidity Agent: http://localhost:9998"
	@echo "Parallel Liquidity Agent: http://localhost:9994"
	@echo "Swap Agent: http://localhost:9995"
	@echo ""
	@echo "Starting all agents in parallel..."
	@make -j5 dev-orchestrator dev-balance dev-liquidity dev-parallel-liquidity dev-swap

# Production builds
build-frontend:
	@echo "Building frontend for production..."
	cd frontend && npm run build

build-backend:
	@echo "Checking backend dependencies..."
	cd backend && uv sync --frozen

# Formatting
format:
	@echo "Formatting all workspaces..."
	$(MAKE) format-backend
	$(MAKE) format-frontend

format-backend:
	@echo "Formatting backend (ruff check --fix + ruff format)..."
	cd backend && uv sync --extra dev && (uv run ruff check --fix . || true) && uv run ruff format .

format-frontend:
	@echo "Formatting frontend (prettier write)..."
	cd frontend && npm run format --silent

# Convenience so `make format backend` works (multi-target):
backend: format-backend

# Testing
test:
	@echo "Running all tests..."
	cd backend && uv sync --extra test && uv run pytest

test-liquidity:
	@echo "Running liquidity agent tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/liquidity/__test__ -v

test-liquidity-polygon:
	@echo "Running Polygon liquidity tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/liquidity/__test__/test_polygon.py -v

test-liquidity-hedera:
	@echo "Running Hedera liquidity tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/liquidity/__test__/test_hedera.py -v

test-liquidity-all-chains:
	@echo "Running all chains liquidity tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/liquidity/__test__/test_all_chains.py -v

test-balance:
	@echo "Running balance agent tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/balance/__test__ -v

test-balance-polygon:
	@echo "Running Polygon balance tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest -s agents/balance/__test__/test_polygon.py -v

test-balance-hedera:
	@echo "Running Hedera balance tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/balance/__test__/test_hedera.py -v

test-balance-all-chains:
	@echo "Running all chains balance tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/balance/__test__/test_all_chains.py -v

test-balance-integration:
	@echo "Running balance agent integration tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/balance/__test__/test_integration.py -v

test-swap:
	@echo "Running all swap agent tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/swap/__test__/ -v

test-swap-unit:
	@echo "Running swap agent unit tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/swap/__test__/test_query_parser.py agents/swap/__test__/test_response_builder.py agents/swap/__test__/test_swap_executor_service.py -v

test-swap-integration:
	@echo "Running swap agent integration tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/swap/__test__/test_integration.py -v

test-orchestrator:
	@echo "Running all orchestrator agent tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/orchestrator/__test__/ -v

test-orchestrator-unit:
	@echo "Running orchestrator agent unit tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/orchestrator/__test__/test_agent.py -v

test-orchestrator-integration:
	@echo "Running orchestrator agent integration tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/orchestrator/__test__/test_integration.py -v

test-parallel-liquidity:
	@echo "Running all parallel liquidity agent tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/parallel_liquidity/__test__/ -v

test-parallel-liquidity-unit:
	@echo "Running parallel liquidity agent unit tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/parallel_liquidity/__test__/test_token_pair_extraction.py agents/parallel_liquidity/__test__/test_result_combination.py agents/parallel_liquidity/__test__/test_sub_agents.py -v

test-parallel-liquidity-integration:
	@echo "Running parallel liquidity agent integration tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest agents/parallel_liquidity/__test__/test_integration.py -v

test-pools:
	@echo "Running pools tests (Uniswap V3 pool address tests)..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest lib/shared/blockchain/pools/__test__/test_uniswap_v3_pool.py -v

test-liquidity-blockchain:
	@echo "Running liquidity blockchain tests (liquidity and slot0)..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest lib/shared/blockchain/liquidity/__test__/test_liquidity.py -v -s

test-tokens:
	@echo "Running all token tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest lib/shared/blockchain/tokens/__test__/ lib/shared/blockchain/tokens/constants/__test__/ -v

test-tokens-constants:
	@echo "Running token constants tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest lib/shared/blockchain/tokens/constants/__test__/test_token_constants.py -v

test-tokens-address:
	@echo "Running token address function tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest lib/shared/blockchain/tokens/__test__/test_token_address.py -v

test-balance-shared:
	@echo "Running shared balance library tests..."
	cd backend && uv sync --extra test && PYTHONPATH=. uv run pytest lib/shared/blockchain/balance/__test__/test_balance.py -v

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

