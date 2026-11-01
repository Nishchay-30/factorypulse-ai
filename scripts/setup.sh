#!/usr/bin/env bash
# ==============================================================================
# FactoryPulse AI - Complete Project Setup Script
# Initializes virtualenv, installs requirements, seeds database, and trains ML model
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "==================================================================="
echo "FactoryPulse AI — Smart Factory Bottleneck Prediction Setup"
echo "==================================================================="

# 1. Check or create .env
if [ ! -f .env ]; then
    echo "[Setup] Creating .env from .env.example..."
    cp .env.example .env
fi

# 2. Virtual environment setup
if [ ! -d .venv ]; then
    echo "[Setup] Creating Python virtual environment..."
    python3 -m venv --system-site-packages .venv
fi

source .venv/bin/activate
echo "[Setup] Active Python: $(which python3)"

# 3. Create required directories
mkdir -p data/csv data/database data/synthetic ml/models

# 4. Initialize SQLite database & default credentials
echo "[Setup] Initializing SQLite database schema and seeding user accounts..."
python3 -c "
from src.database.db import db
from src.common.auth import seed_default_users
db.init_db()
seed_default_users()
print('Database & accounts verified.')
"

# 5. Generate synthetic training dataset & train model
if [ ! -f ml/models/bottleneck_rf_model.joblib ]; then
    echo "[Setup] Generating synthetic training data (15 episodes)..."
    python3 ml/generate_dataset.py
    echo "[Setup] Training Random Forest Bottleneck Prediction model..."
    python3 ml/train.py
fi

echo "==================================================================="
echo "Setup completed successfully! You can now start the demonstration."
echo "Execute: bash scripts/start_demo.sh"
echo "==================================================================="

