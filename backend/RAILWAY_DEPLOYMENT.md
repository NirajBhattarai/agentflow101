# Railway Deployment Guide for AgentFlow101

This guide will help you deploy the AgentFlow101 backend with all agents to Railway.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be on GitHub
3. **Google API Key**: Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Step 1: Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `agentflow101` repository
5. Select the repository

## Step 2: Configure the Service

1. Railway will detect the `railway.json` or `railway.toml` file
2. If not detected, click "Add Service" → "GitHub Repo" → Select your repo
3. Set the **Root Directory** to `backend` (if deploying from monorepo)

## Step 3: Set Environment Variables

In Railway dashboard, go to your service → **Variables** tab and add:

### Required Variables

```bash
GOOGLE_API_KEY=your_google_api_key_here
# OR
GEMINI_API_KEY=your_gemini_api_key_here

HEDERA_NETWORK=testnet
```

### Optional Port Configuration (defaults are fine)

```bash
ORCHESTRATOR_PORT=9000
BALANCE_PORT=9997
LIQUIDITY_PORT=9998
BRIDGE_PORT=9996
SWAP_PORT=9995
```

### Railway Auto-Generated (don't set manually)

Railway will automatically set:
- `PORT` - Main port (we use 8000)
- `RAILWAY_ENVIRONMENT` - Environment name
- `RAILWAY_PROJECT_ID` - Project ID

## Step 4: Configure Ports

Since we're running multiple services, you need to configure Railway to expose multiple ports:

1. Go to your service → **Settings** → **Networking**
2. Add these **Public Domains** or use Railway's auto-generated domains:
   - Main Backend: `your-service.railway.app` (port 8000)
   - Orchestrator: `orchestrator.railway.app` (port 9000) - **OR** use a separate service
   - Balance: `balance.railway.app` (port 9997) - **OR** use a separate service
   - Liquidity: `liquidity.railway.app` (port 9998) - **OR** use a separate service
   - Bridge: `bridge.railway.app` (port 9996) - **OR** use a separate service
   - Swap: `swap.railway.app` (port 9995) - **OR** use a separate service

### Option A: Single Service (Simpler, Cheaper)

All agents run in one service. You'll need to use Railway's internal networking or expose one main port and use that for the frontend.

**Recommended**: Expose only port 8000 (main backend) and configure agents to use internal URLs.

### Option B: Multiple Services (More Control, More Cost)

Create separate Railway services for each agent:
1. Main Backend Service (port 8000)
2. Orchestrator Service (port 9000)
3. Balance Agent Service (port 9997)
4. Liquidity Agent Service (port 9998)
5. Bridge Agent Service (port 9996)
6. Swap Agent Service (port 9995)

## Step 5: Update Frontend Environment Variables

Update your frontend `.env.local` or environment variables:

```bash
# Main backend
NEXT_PUBLIC_API_URL=https://your-backend.railway.app

# Agent URLs (if using separate services)
ORCHESTRATOR_URL=https://your-orchestrator.railway.app
BALANCE_AGENT_URL=https://your-balance.railway.app
LIQUIDITY_AGENT_URL=https://your-liquidity.railway.app
BRIDGE_AGENT_URL=https://your-bridge.railway.app
SWAP_AGENT_URL=https://your-swap.railway.app
```

## Step 6: Deploy

1. Railway will automatically deploy when you push to your main branch
2. Or click **Deploy** in the Railway dashboard
3. Check the **Logs** tab to see all services starting

## Step 7: Verify

Check the logs to see:
```
🚀 Starting all AgentFlow services...
📡 Starting main backend on port 8000...
🎯 Starting Orchestrator Agent on port 9000...
💰 Starting Balance Agent on port 9997...
📊 Starting Liquidity Agent on port 9998...
🌉 Starting Bridge Agent on port 9996...
💱 Starting Swap Agent on port 9995...
✅ All services started!
```

## Troubleshooting

### Services Not Starting

1. Check logs in Railway dashboard
2. Verify environment variables are set correctly
3. Check that `GOOGLE_API_KEY` is set
4. Verify Python version (should be 3.11+)

### Port Issues

Railway assigns a random `PORT` environment variable. Our script uses fixed ports, which should work, but if you see port conflicts:

1. Use Railway's `PORT` variable for main backend
2. Update `start.sh` to use `$PORT` instead of hardcoded 8000

### Memory Issues

If you see out-of-memory errors:
1. Upgrade Railway plan (Hobby → Developer)
2. Or split into multiple services (Option B above)

## Cost Estimation

- **Single Service (Option A)**: ~$5/month (Hobby plan)
- **Multiple Services (Option B)**: ~$5-7 per service = $30-42/month

**Recommendation**: Start with Option A (single service) for development/demo.

## Development Mode

For local development with Railway-like setup:

```bash
cd backend
chmod +x start.sh
./start.sh
```

Or use the Makefile:
```bash
make dev-all-agents
```

## Next Steps

1. Set up custom domains (optional)
2. Configure monitoring/alerts
3. Set up CI/CD for auto-deployment
4. Add database if needed (Railway PostgreSQL)

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway

