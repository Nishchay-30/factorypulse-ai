#!/usr/bin/env bash
# ==============================================================================
# FactoryPulse AI - Main College Demonstration Launcher
# Launches local broker check, starts FastAPI and Streamlit dashboard
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"
source .venv/bin/activate

echo "==================================================================="
echo "Starting FactoryPulse AI — Smart Factory Bottleneck Prediction"
echo "==================================================================="

# Start FastAPI internal backend in background
echo "[Launcher] Starting FastAPI Internal Alert & Rest Service (Port 8000)..."
python3 -m uvicorn src.api.routes:api_app --host 127.0.0.1 --port 8000 --log-level warning > fastapi.log 2>&1 &
FASTAPI_PID=$!
echo $FASTAPI_PID > .fastapi.pid
echo "[Launcher] FastAPI running on PID $FASTAPI_PID"

# Launch Streamlit Dashboard
echo "[Launcher] Starting FactoryPulse AI Industrial Dashboard (Port 8501)..."
echo "Open browser to: http://localhost:8501"
streamlit run dashboard/app.py --server.port 8501 --server.headless false

