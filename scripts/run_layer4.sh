#!/usr/bin/env bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source .venv/bin/activate

echo "==================================================================="
echo "LAYER 4 ACCEPTANCE TEST: Node-RED Automation & Alert Engine"
echo "==================================================================="

python3 -c "
import json
from pathlib import Path
from src.alerts.engine import AlertEngine
from src.database.db import db

print('[Layer 4] Validating Node-RED flows JSON export...')
flows_path = Path('node_red/flows.json')
assert flows_path.exists(), 'node_red/flows.json missing'
with open(flows_path, 'r', encoding='utf-8') as f:
    flows = json.load(f)
assert isinstance(flows, list) and len(flows) >= 5, 'flows.json is empty or invalid'

node_types = {n.get('type') for n in flows}
print(f'  ✓ Node-RED flow validated ({len(flows)} nodes, types: {node_types})')

print('[Layer 4] Testing Industrial Alert Engine (Debounce & Hysteresis)...')
engine = AlertEngine()
st_id = 'station02'

# Step 1: Single abnormal reading (below warning limit) -> Should NOT fire due to hysteresis
engine.evaluate_station_reading({'station_id': st_id, 'rpm': 750.0, 'queue_length': 18})
state = engine._get_state(st_id, 'RPM_WARNING_LOW')
assert state['consecutive_abnormal'] == 1
assert state['is_active'] is False
print('  ✓ Hysteresis confirmed: Reading 1 did not prematurely fire alert.')

# Step 2: Consecutive abnormal readings to reach threshold (3 counts)
engine.evaluate_station_reading({'station_id': st_id, 'rpm': 750.0, 'queue_length': 18})
engine.evaluate_station_reading({'station_id': st_id, 'rpm': 750.0, 'queue_length': 18})
assert state['consecutive_abnormal'] >= 3
assert state['is_active'] is True
print('  ✓ Alert fired after 3 consecutive abnormal readings.')

# Step 3: Check database for recorded alert
recent_alerts = db.get_recent_alerts(limit=5)
assert len(recent_alerts) > 0
print(f'  ✓ Alert persisted in SQLite: [{recent_alerts[0][\"severity\"]}] {recent_alerts[0][\"message\"]}')

print('[Layer 4] ACCEPTANCE CRITERIA MET: Node-RED flows verified and Alert Engine operational.')
"

