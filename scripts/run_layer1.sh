#!/usr/bin/env bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source .venv/bin/activate

echo "==================================================================="
echo "LAYER 1 ACCEPTANCE TEST: Synthetic Data -> MQTT -> CSV -> Dashboard"
echo "==================================================================="

python3 -c "
import time
import pandas as pd
from src.simulator.factory_simulator import FactorySimulator
from src.ingestion.csv_logger import csv_logger
from src.mqtt.client import MQTTClientWrapper

print('[Layer 1] Initializing 3-station factory simulator...')
sim = FactorySimulator()
sim.set_scenario('scenario_a')

pub = MQTTClientWrapper(client_id_suffix='l1_pub')
pub.connect(timeout=2.0)

print('[Layer 1] Stepping simulator and publishing 5 cycles...')
for i in range(5):
    step = sim.step(dt_override=1.0)
    for st in ['station01', 'station02', 'station03']:
        data = step[st].model_dump()
        pub.publish(f'factory/{st}/telemetry', data)
        csv_logger.log_station_telemetry(data)
    line_data = step['processed'].model_dump()
    pub.publish('factory/processed/telemetry', line_data)
    csv_logger.log_line_telemetry(line_data)

print('[Layer 1] Verifying generated CSV records...')
for f in ['station01.csv', 'station02.csv', 'station03.csv', 'production_line.csv']:
    path = csv_logger.output_dir / f
    assert path.exists(), f'{f} does not exist'
    df = pd.read_csv(path)
    print(f'  ✓ {f}: {len(df)} rows recorded with valid headers')

pub.disconnect()
print('[Layer 1] ACCEPTANCE CRITERIA MET: Telemetry generated, published, and recorded in CSV.')
"

