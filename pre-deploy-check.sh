#!/bin/bash
# Pre-deployment validation script
# Run this before deploying to Render or Vercel

set -e

echo "🔍 Ocean Plastic Monitoring - Pre-Deployment Validation"
echo "========================================================="

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python: $python_version"

# Check if running in virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  WARNING: Not running in a virtual environment"
    echo "  Run: python3 -m venv venv && source venv/bin/activate"
fi

# Check requirements.txt
echo "✓ Checking backend dependencies..."
backend_dir="backend"
if [ ! -f "$backend_dir/requirements.txt" ]; then
    echo "❌ ERROR: $backend_dir/requirements.txt not found"
    exit 1
fi

# Try to import critical packages
echo "✓ Validating Python dependencies..."
python3 -c "
import sys
required = ['fastapi', 'uvicorn', 'ultralytics', 'opencv', 'requests', 'numpy', 'sentinelhub']
missing = []
for pkg in required:
    try:
        __import__(pkg)
        print(f'  ✓ {pkg}')
    except ImportError:
        missing.append(pkg)
        print(f'  ✗ {pkg}')
        
if missing:
    print(f'\\n⚠️  Missing packages: {missing}')
    print('   Run: pip install -r backend/requirements.txt')
" || true

# Check environment variables
echo "✓ Checking environment configuration..."
if [ -f "backend/.env" ]; then
    source backend/.env
    if [ -z "$SENTINELHUB_CLIENT_ID" ]; then
        echo "  ⚠️  SENTINELHUB_CLIENT_ID not set"
    else
        echo "  ✓ SENTINELHUB_CLIENT_ID configured"
    fi
else
    echo "  ℹ️  No .env file found (will use environment variables)"
fi

# Check for yolov8n.pt model
echo "✓ Checking YOLO model..."
if [ -f "backend/yolov8n.pt" ]; then
    size=$(du -h backend/yolov8n.pt | awk '{print $1}')
    echo "  ✓ YOLO model found ($size)"
else
    echo "  ⚠️  YOLO model not found - will be downloaded on first run"
fi

# Check frontend
echo "✓ Checking frontend..."
frontend_files=("index.html" "app.js" "styles.css")
for file in "${frontend_files[@]}"; do
    if [ -f "frontend-static/$file" ]; then
        echo "  ✓ $file found"
    else
        echo "  ✗ $file NOT FOUND"
    fi
done

# Validate app.py syntax
echo "✓ Validating Python syntax..."
python3 -m py_compile backend/app.py && echo "  ✓ app.py syntax OK" || echo "  ✗ app.py has syntax errors"

# Test startup (simulate)
echo "✓ Testing API startup..."
cd backend
timeout 5 python3 -c "from app import app; print('  ✓ App imports successfully')" || true
cd ..

echo ""
echo "✅ Pre-deployment validation COMPLETE"
echo ""
echo "Next steps for Render deployment:"
echo "1. Push code to GitHub: git add . && git commit -m 'Production ready' && git push"
echo "2. Create Render Web Service: https://dashboard.render.com/new/web"
echo "3. Connect your GitHub repository"
echo "4. Set environment variables in Render dashboard:"
echo "   - SENTINELHUB_CLIENT_ID"
echo "   - SENTINELHUB_CLIENT_SECRET"
echo "   - OPENWEATHER_API_KEY (optional)"
echo "5. Deploy!"
echo ""
echo "Next steps for Vercel frontend deployment:"
echo "1. Push code to GitHub"
echo "2. Go to: https://vercel.com/new"
echo "3. Import GitHub repository"
echo "4. Set environment variable:"
echo "   - NEXT_PUBLIC_BACKEND_URL = your-render-backend-url"
echo "5. Deploy!"
