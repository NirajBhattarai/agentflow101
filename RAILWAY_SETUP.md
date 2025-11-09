# Railway Setup Instructions

## Issue: Railpack Auto-Detection

If you see the error:
```
⚠ Script start.sh not found
✖ Railpack could not determine how to build the app.
```

This means Railway is trying to use Railpack (auto-detection) instead of Dockerfile.

## Solution: Configure Railway to Use Dockerfile

### Option 1: Set Root Directory in Railway Dashboard (Recommended)

1. Go to your Railway project
2. Click on your service
3. Go to **Settings** tab
4. Scroll to **Root Directory**
5. Set it to: `backend`
6. Save and redeploy

This tells Railway to build from the `backend/` directory where the Dockerfile is located.

### Option 2: Use Railway Configuration File

The `railway.json` in the root should tell Railway to use Dockerfile, but you may need to:

1. Go to Railway dashboard → Your service → **Settings**
2. Under **Build & Deploy**, ensure:
   - **Builder**: Dockerfile
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Root Directory**: Leave empty (or set to `.`)

### Option 3: Manual Dockerfile Selection

1. In Railway dashboard → Your service
2. Go to **Settings** → **Build**
3. Select **Dockerfile** as the builder
4. Set **Dockerfile Path** to: `backend/Dockerfile`
5. Set **Docker Context** to: `.` (root of repo)

## Verify Configuration

After setting up, the build should:
1. Use the Dockerfile from `backend/Dockerfile`
2. Build context from repository root
3. Copy files from `backend/` directory
4. Run `./start.sh` inside the container

## Environment Variables

Don't forget to set in Railway dashboard:
- `GOOGLE_API_KEY=your_key`
- `HEDERA_NETWORK=testnet`

## Troubleshooting

If still having issues:

1. **Check build logs** - Look for Docker build output
2. **Verify Dockerfile path** - Should be `backend/Dockerfile`
3. **Check file permissions** - `start.sh` should be executable (we set this in Dockerfile)
4. **Try redeploying** - Sometimes Railway caches the old config

## Alternative: Use Railway CLI

You can also configure via Railway CLI:

```bash
railway link
railway variables set GOOGLE_API_KEY=your_key
railway variables set HEDERA_NETWORK=testnet
railway up
```

