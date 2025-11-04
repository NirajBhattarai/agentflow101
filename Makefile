.PHONY: help install-frontend install-backend install dev-frontend dev-backend dev build-frontend build-backend test clean

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
	@echo "Build:"
	@echo "  make build-frontend      - Build frontend for production"
	@echo "  make build-backend       - Build backend (check dependencies)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean               - Clean build artifacts and dependencies"
	@echo "  make test                - Run tests (placeholder)"

# Installation
install: install-frontend install-backend

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && uv sync

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

# Production builds
build-frontend:
	@echo "Building frontend for production..."
	cd frontend && npm run build

build-backend:
	@echo "Checking backend dependencies..."
	cd backend && uv sync --frozen

# Testing
test:
	@echo "Running tests..."
	@echo "Frontend tests: cd frontend && npm test"
	@echo "Backend tests: cd backend && uv run pytest"

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

