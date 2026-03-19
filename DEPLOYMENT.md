# 🚀 Production Deployment Guide

**Ocean Plastic Monitoring System - Render + Vercel Deployment**

---

## 📋 Pre-Deployment Checklist

### ✅ Backend (Render - Python Web Service)

- [ ] All files committed to Git
- [ ] `.env.example` updated with all required variables
- [ ] `requirements.txt` has pinned versions
- [ ] `render.yaml` created and configured
- [ ] Environment variables validated (run `bash pre-deploy-check.sh`)
- [ ] YOLO model present or will download on startup
- [ ] No hardcoded localhost URLs
- [ ] Logging system configured
- [ ] Health check endpoint `/health` responds 200 OK

### ✅ Frontend (Vercel - Static)

- [ ] All JS/CSS/HTML files optimized
- [ ] `vercel.json` created
- [ ] API URL uses `window.BACKEND_URL` not hardcoded localhost
- [ ] Error handling UI implemented (error toast notifications)
- [ ] Loading indicator implemented
- [ ] Favicon present (optional)

### ✅ DevOps

- [ ] GitHub repository created and code pushed
- [ ] Render account created at render.com
- [ ] Vercel account created at vercel.com  
- [ ] GitHub OAuth tokens generated
- [ ] Sentinel Hub credentials obtained (sentinel-hub.com)
- [ ] OpenWeather API key obtained (optional - Open-Meteo fallback)

---

## 🔧 Step 1: Setup GitHub Repository

```bash
# From parent directory
cd /home/loki/projects/ocean_skimmer/ocean-watch-ai

# Initialize if not already
git init

# Add all files
git add .

# Commit
git commit -m "Production-ready Ocean Plastic Monitoring System

- YOLO model preloading for <10s cold start
- Satellite image size optimized (768→384)
- Structured logging with request tracking
- Graceful degradation on API failures
- Environment variable validation
- Frontend API URL configuration
- Error toast notifications
- Deployment configs (render.yaml, vercel.json)"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/ocean-plastic-monitoring.git
git branch -M main
git push -u origin main
```

---

## 🎯 Step 2: Deploy Backend to Render

### 2.1 Create Render Account

1. Go to https://render.com
2. Sign up with GitHub
3. Authorize repository access

### 2.2 Create Web Service

1. Dashboard → New → Web Service
2. Select your GitHub repository
3. Configure:
   - **Name:** `ocean-plastic-api` (or similar)
   - **Environment:** `Python 3.11`
   - **Root Directory:** `backend/` ⚠️ **CRITICAL - Must set this**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** See below
   - **Plan:** Free tier (2 concurrent requests) or Starter ($7/month, 3 vCPU, 512MB RAM)

### 2.3 Start Command

**In Render Dashboard, set the Start Command field to:**

```
gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT} --timeout 60 --access-logfile - app:app
```

**IMPORTANT:** 
- Copy and paste the command EXACTLY as shown above
- Do NOT add `bash` or any shell prefix
- This runs from the backend directory automatically

### 2.4 Environment Variables

Set these in Render Dashboard → Environment:

```
SENTINELHUB_CLIENT_ID = your_client_id_here
SENTINELHUB_CLIENT_SECRET = your_client_secret_here
SENTINELHUB_INSTANCE_ID = (leave empty if not needed)
OPENWEATHER_API_KEY = your_api_key (optional, Open-Meteo fallback)
SATELLITE_IMAGE_WIDTH = 384
SATELLITE_IMAGE_HEIGHT = 384
REQUEST_TIMEOUT_SECONDS = 15
REQUEST_TIMEOUT_ANALYZE_SECONDS = 60
EXTERNAL_API_MAX_RETRIES = 3
EXTERNAL_API_BACKOFF_SECONDS = 1.5
ENABLE_RESPONSE_CACHING = true
RESPONSE_CACHE_TTL_SECONDS = 1800
```

### 2.5 Deploy

1. Click **Create Web Service**
2. Wait for build (~2-3 minutes)
3. Check logs: Dashboard → Logs
4. Verify: `https://your-backend-name.onrender.com/health` should return `{"status":"ok"}`

### 2.6 Get Backend URL

Once deployed, you'll have a URL like:
```
https://ocean-plastic-api-abc123.onrender.com
```

**Keep this URL - you'll need it for frontend deployment**

---

## 🌐 Step 3: Deploy Frontend to Vercel

### 3.1 Create Vercel Account

1. Go to https://vercel.com
2. Sign up with GitHub
3. Authorize repository access

### 3.2 Import Project

1. Dashboard → Add New → Project
2. Select **Import Git Repository**
3. Paste your repository URL
4. Click **Import**

### 3.3 Configure Frontend

1. **Project Settings:**
   - Framework: `Other` (static sites)
   - Build Command: (leave empty)
   - Output Directory: `.` (current directory)

2. **Root Directory:** Set to `frontend-static/`

3. **Environment Variables:**
   - Add `NEXT_PUBLIC_BACKEND_URL=https://ocean-plastic-api-abc123.onrender.com`
   - (Replace with your actual Render backend URL from Step 2.6)

### 3.4 Deploy

1. Click **Deploy**
2. Wait for build (~1 minute)
3. Get your Vercel URL: `https://your-project-name.vercel.app`

### 3.5 Verify

1. Open frontend URL in browser
2. Click "Analyze" button
3. Should see map with plastic density visualization
4. Check browser console for any errors

---

## 🧪 Step 4: Validation & Testing

### 4.1 Test Backend Health

```bash
curl https://ocean-plastic-api-abc123.onrender.com/health
# Should return: {"status":"ok"}
```

### 4.2 Test Analysis Endpoint

```bash
curl -X POST https://ocean-plastic-api-abc123.onrender.com/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "bbox": {
      "min_lat": 12.0,
      "max_lat": 18.0,
      "min_lon": 86.0,
      "max_lon": 92.0
    }
  }'
```

Expected response:
```json
{
  "status": "ok" or "degraded",
  "message": null or "Using last available data",
  "bbox": {...},
  "current_location": {...},
  "predicted_location": {...},
  "wind": {...},
  "current": {...},
  "satellite": {...},
  "detections": [...]
}
```

### 4.3 Test Frontend

1. Open `https://your-project-name.vercel.app`
2. Zoom into a region (< 25 sq degrees)
3. Click "Analyze"
4. Wait for results (first request: ~30s for YOLO model, ~10s after)
5. Should see:
   - Map with blue requested region
   - Current location marker (blue)
   - Predicted location marker (orange)
   - Heatmap of plastic detections
   - Updated metrics (density, cluster count)
   - Wind/current data in panels

### 4.4 Simulate API Failures

Backend automatically responds with `status: "degraded"` when:
- Sentinel Hub is unavailable
- Wind API fails
- Ocean current API fails

Frontend will show message: "Degraded: Using last available data"

---

## 📊 Monitoring & Logs

### Render Backend Logs

1. Render Dashboard → Select your service
2. **Logs** tab shows real-time service output
3. Look for:
   - Startup messages: "✅ YOLO model loaded successfully"
   - Request logs: `[req-id] POST /analyze`
   - Errors: "❌" entries

### Vercel Frontend Logs

1. Vercel Dashboard → Select project
2. **Deployments** tab
3. Click latest deployment
4. **Logs** tab shows build output

### Local Testing Before Deploy

```bash
# Start backend locally
cd backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start frontend
python -m http.server 5500 --directory frontend-static

# Open http://localhost:5500 in browser
```

---

## 🚨 Troubleshooting

### Backend Won't Start

**Error: "ModuleNotFoundError: No module named 'app'"**
- Solution: In Render Dashboard, set **Root Directory** to `backend/` (Step 2.2)
- This tells Render where the app.py file is located
- Rebuild service after changing this setting

**Error: "SENTINELHUB credentials are not configured"**
- Solution: Add SENTINELHUB_CLIENT_ID and CLIENT_SECRET to Render environment

**Error: "No module named 'sentinelhub'"**
- Solution: Ensure `requirements.txt` is in `backend/` directory
- Render is looking for dependencies from that path

**Error: "YOLO model not found"**
- Solution: First request will download (~200MB, ~60s)
- Subsequent requests will use cached model

### Frontend Won't Connect

**Error: "Failed to connect to Backend"**
- Solution: Check NEXT_PUBLIC_BACKEND_URL environment variable
- Should be: `https://your-backend-url.onrender.com` (no trailing slash)

**CORS Error:**
- Backend already has CORS enabled
- If still seeing error, check browser console for actual URL being called

### Response Time Is Slow

**First request takes 60+ seconds:**
- Normal - YOLO model is loading (~30s)
- Subsequent requests: 5-15s (depends on API response times)

**Subsequent requests still slow:**
- Check individual API performance:
  - Sentinel Hub: ~3-5s
  - Wind API: ~1-2s
  - Ocean Current: ~2-3s
- Total: ~10-15s typical

### Getting 502 Errors

Should NOT happen - system falls back gracefully. If it does:
1. Check Render logs for actual error
2. Verify all environment variables are set
3. Restart service: Render Dashboard → Service → Restart

---

## 💰 Cost Estimation (Monthly)

| Service | Tier | Cost | Notes |
|---------|------|------|-------|
| **Render Backend** | Starter | $7 | 3 vCPU, 512MB RAM, auto-scaling |
| **Vercel Frontend** | Pro | $20 | Analytics, edge functions (optional) |
| **APIs** | Free | $0 | Sentinel Hub (free tier: 100 req/day) |
| | | | Open-Meteo (free tier: 450 req/day) |
| **Total** | | ~$27/month | Scales with usage |

---

## 🔐 Security Notes

1. **Never commit `.env` file** - Only push `.env.example`
2. **Environment variables** stored securely in Render/Vercel dashboards
3. **API keys** never exposed in frontend code
4. **CORS** configured to allow all origins (change if needed)
5. **HTTPS** used automatically on both Render and Vercel

---

## 🔄 Continuous Deployment

After initial setup, every `git push` to main branch automatically:
1. Triggers Render build → deploys backend
2. Triggers Vercel build → deploys frontend

To make changes:
```bash
# Make code changes
git add .
git commit -m "Fix: description of changes"
git push origin main

# Watch Render/Vercel dashboards for deployment status
```

---

## 📞 Support

- **Render Support:** https://render.com/docs
- **Vercel Support:** https://vercel.com/docs
- **Sentinel Hub:** https://sentinel-hub.com/develop/documentation/
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **YOLO Docs:** https://docs.ultralytics.com/

---

**Deployment Complete! 🎉**

Your Ocean Plastic Monitoring System is now live and ready for production use!
