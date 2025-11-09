#!/bin/bash
# Development script to run all agents locally
# This is similar to start.sh but with better logging and process management

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting AgentFlow101 in Development Mode${NC}"
echo ""

# Check for API key
if [ -z "$GOOGLE_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Warning: No API key found!${NC}"
    echo "   Set either GOOGLE_API_KEY or GEMINI_API_KEY environment variable"
    echo "   Example: export GOOGLE_API_KEY='your-key-here'"
    echo ""
fi

# Create logs directory
mkdir -p logs

# Function to start a service
start_service() {
    local name=$1
    local command=$2
    local port=$3
    
    echo -e "${BLUE}Starting $name on port $port...${NC}"
    uv run $command > "logs/${name}.log" 2>&1 &
    local pid=$!
    echo "$pid" > "logs/${name}.pid"
    echo "  ✓ $name started (PID: $pid, Port: $port)"
    sleep 1
}

# Clean up old logs and PIDs
rm -f logs/*.pid logs/*.log

# Start all services
start_service "main-backend" "uvicorn main:app --host 0.0.0.0 --port 8000 --reload" "8000"
start_service "orchestrator" "-m agents.orchestrator.orchestrator" "9000"
start_service "balance-agent" "-m agents.balance" "9997"
start_service "liquidity-agent" "-m agents.liquidity" "9998"
start_service "bridge-agent" "-m agents.bridge" "9996"
start_service "swap-agent" "-m agents.swap" "9995"

echo ""
echo -e "${GREEN}✅ All services started!${NC}"
echo ""
echo "📡 Service URLs:"
echo "   Main Backend:    http://localhost:8000"
echo "   API Docs:        http://localhost:8000/docs"
echo "   Orchestrator:    http://localhost:9000"
echo "   Balance Agent:   http://localhost:9997"
echo "   Liquidity Agent: http://localhost:9998"
echo "   Bridge Agent:    http://localhost:9996"
echo "   Swap Agent:      http://localhost:9995"
echo ""
echo "📋 Logs are in the 'logs/' directory"
echo "   View logs: tail -f logs/<service-name>.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping all services...${NC}"
    
    # Kill all processes from PID files
    for pidfile in logs/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            kill $pid 2>/dev/null || true
            echo "  Stopped PID: $pid"
        fi
    done
    
    # Clean up PID files
    rm -f logs/*.pid
    
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Trap SIGTERM and SIGINT
trap cleanup SIGTERM SIGINT

# Wait for user interrupt
wait

