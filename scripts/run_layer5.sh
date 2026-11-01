#!/usr/bin/env bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source .venv/bin/activate

echo "==================================================================="
echo "LAYER 5 ACCEPTANCE TEST: AI/ML Bottleneck Prediction & Auth"
echo "==================================================================="

python3 -c "
import json
from src.prediction.predictor import RealTimePredictor
from src.common.auth import authenticate_user, verify_password, hash_password
from src.database.db import db
from src.common.config import config

print('[Layer 5] Testing Password Authentication & Salted Hashing...')
h, s = hash_password('TestPass123')
assert verify_password('TestPass123', s, h) is True
assert verify_password('WrongPass', s, h) is False

admin_user = authenticate_user(config.ADMIN_USERNAME, config.ADMIN_INITIAL_PASSWORD)
assert admin_user is not None
assert admin_user['role'] == 'admin'
print(f'  ✓ Authenticated Administrator: {admin_user[\"username\"]} (Role: {admin_user[\"role\"]})')

op_user = authenticate_user(config.OPERATOR_USERNAME, config.OPERATOR_INITIAL_PASSWORD)
assert op_user is not None
assert op_user['role'] == 'operator'
print(f'  ✓ Authenticated Operator: {op_user[\"username\"]} (Role: {op_user[\"role\"]})')

print('[Layer 5] Verifying Serialized Random Forest Model & Metadata...')
meta = db.get_active_model_metadata()
assert meta is not None, 'No active model metadata found in database'
print(f'  ✓ Active Model Version: {meta[\"model_version\"]}')
print(f'  ✓ Test Accuracy:        {meta[\"accuracy\"]*100:.2f}%')
print(f'  ✓ Test F1-Score:        {meta[\"f1_score\"]:.4f}')

print('[Layer 5] Testing Real-Time Inference Daemon...')
predictor = RealTimePredictor()
test_reading = {
    'station_id': 'station02',
    'rpm': 600.0,
    'cycle_time': 9.0,
    'throughput': 6.0,
    'utilization': 0.4,
    'queue_length': 22,
    'status': 'WARNING'
}
pred = predictor.process_reading(test_reading)
assert pred is not None
print(f'  ✓ Prediction Horizon:  {pred.prediction_horizon_sec} seconds')
print(f'  ✓ Risk Probability:    {pred.risk_probability*100:.1f}%')
print(f'  ✓ Bottleneck Detected: {pred.bottleneck_predicted}')
print(f'  ✓ Predicted Station:   {pred.predicted_station}')

print('[Layer 5] ACCEPTANCE CRITERIA MET: ML pipeline trained, evaluated, inferencing in real-time with authentication protection.')
"

