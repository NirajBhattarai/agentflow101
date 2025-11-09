# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files (from backend directory)
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code (from backend directory)
COPY backend/ .

# Expose ports for all services
# Main backend: 8000
# Orchestrator: 9000
# Balance: 9997
# Bridge: 9996
# Swap: 9995
# Liquidity: 9998
EXPOSE 8000 9000 9995 9996 9997 9998

# Make start script executable
RUN chmod +x start.sh dev-start.sh

# Use the start script
CMD ["./start.sh"]

