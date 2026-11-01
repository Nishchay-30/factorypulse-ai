#!/usr/bin/env bash
# ==============================================================================
# FactoryPulse AI - Main Demonstration Shutdown Script
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "Shutting down FactoryPulse AI services..."

# Kill FastAPI if running
if [ -f .fastapi.pid ]; then
    PID=$(cat .fastapi.pid)
    kill -9 $PID 2>/dev/null || true
    rm -f .fastapi.pid
    echo "Stopped FastAPI (PID $PID)."
fi

# Kill any leftover Streamlit instances on port 8501
pkill -f "streamlit run dashboard/app.py" 2>/dev/null || true

echo "All FactoryPulse AI services stopped."

