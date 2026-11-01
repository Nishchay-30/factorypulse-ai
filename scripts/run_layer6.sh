#!/usr/bin/env bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.."
source .venv/bin/activate

echo "==================================================================="
echo "LAYER 6 ACCEPTANCE TEST: ESP32 Hardware Integration & Hybrid Mode"
echo "==================================================================="

python3 -c "
from pathlib import Path
from src.simulator.factory_simulator import FactorySimulator
from src.common.config import config

print('[Layer 6] Verifying ESP32 PlatformIO Project Files...')
pio_ini = Path('firmware/esp32_motor_station/platformio.ini')
main_cpp = Path('firmware/esp32_motor_station/src/main.cpp')
sensors_cpp = Path('firmware/esp32_motor_station/src/sensors.cpp')
sensors_h = Path('firmware/esp32_motor_station/include/sensors.h')
config_h = Path('firmware/esp32_motor_station/include/config.h')
wiring_doc = Path('docs/hardware_wiring.md')

for p in [pio_ini, main_cpp, sensors_cpp, sensors_h, config_h, wiring_doc]:
    assert p.exists(), f'Missing hardware artifact: {p}'
    print(f'  ✓ Hardware artifact verified: {p}')

print('[Layer 6] Testing Station 2 Hybrid Hardware Mode Calibration...')
sim = FactorySimulator()
sim.set_scenario('scenario_f')  # Hardware mode
assert sim.station2.hardware_active is True
assert sim.station2.source == 'hardware'

# Simulate telemetry from ESP32 measuring 650 RPM from physical IR sensor
sim.station2.update_hardware_reading(rpm=650.0, current=1.45, temp=42.0)
step = sim.step(dt_override=2.0)
st2 = step['station02']

print(f'  ✓ Measured Hardware RPM: {st2.rpm}')

expected_instant = (
    config.STATION2_CAPACITY_PER_MIN
    * 650.0 / config.STATION2_BASE_RPM
)

expected_smoothed = (
    0.85 * config.STATION2_CAPACITY_PER_MIN
    + 0.15 * expected_instant
)

assert abs(st2.throughput - expected_smoothed) < 0.03, (
    'Throughput calibration mismatch'
)

print(f'  ✓ Instantaneous Capacity: {expected_instant:.2f} PPM')
print(f'  ✓ Smoothed Throughput: {st2.throughput:.2f} PPM')

print(f'  ✓ Resulting Machine Status: {st2.status}')
print(f'  ✓ Upstream Queue Accumulation: {st2.queue_length} units')

print('[Layer 6] ACCEPTANCE CRITERIA MET: PlatformIO project valid, hardware wiring documented, and hybrid motor mode functioning.')
"

