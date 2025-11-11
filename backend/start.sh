#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Use PORT environment variable if set, otherwise default to 8000
MAIN_PORT=${PORT:-8000}

# Start all services in background
echo "🚀 Starting all AgentFlow services..."

# Start main backend
echo "📡 Starting main backend on port $MAIN_PORT..."
uv run uvicorn main:app --host 0.0.0.0 --port $MAIN_PORT &
BACKEND_PID=$!

# Start Orchestrator Agent (port 9000)
echo "🎯 Starting Orchestrator Agent on port 9000..."
uv run -m agents.orchestrator.orchestrator &
ORCHESTRATOR_PID=$!

# Start Balance Agent (port 9997)
echo "💰 Starting Balance Agent on port 9997..."
uv run -m agents.balance &
BALANCE_PID=$!

# Start Liquidity Agent (port 9998)
echo "📊 Starting Liquidity Agent on port 9998..."
uv run -m agents.liquidity &
LIQUIDITY_PID=$!

# Start Bridge Agent (port 9996)
echo "🌉 Starting Bridge Agent on port 9996..."
uv run -m agents.bridge &
BRIDGE_PID=$!

# Start Swap Agent (port 9995)
echo "💱 Starting Swap Agent on port 9995..."
uv run -m agents.swap &
SWAP_PID=$!

# Start Parallel Liquidity Agent (port 9994)
echo "💧🚀 Starting Parallel Liquidity Agent on port 9994..."
uv run -m agents.parallel_liquidity &
PARALLEL_LIQUIDITY_PID=$!

# Wait for all processes
echo "✅ All services started!"
echo "   Main Backend: http://0.0.0.0:8000"
echo "   Orchestrator: http://0.0.0.0:9000"
echo "   Balance Agent: http://0.0.0.0:9997"
echo "   Liquidity Agent: http://0.0.0.0:9998"
echo "   Bridge Agent: http://0.0.0.0:9996"
echo "   Swap Agent: http://0.0.0.0:9995"
echo "   Parallel Liquidity Agent: http://0.0.0.0:9994"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $BACKEND_PID $ORCHESTRATOR_PID $BALANCE_PID $LIQUIDITY_PID $BRIDGE_PID $SWAP_PID $PARALLEL_LIQUIDITY_PID 2>/dev/null || true
    exit 0
}

# Trap SIGTERM and SIGINT
trap cleanup SIGTERM SIGINT

# Wait for all background processes
wait

