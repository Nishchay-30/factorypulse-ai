# Layer 1 — Synthetic Data → MQTT → CSV → Dashboard
## Architecture, Verification & Acceptance Criteria

### 1. Objective
Simulate a three-stage manufacturing line (Cutting -> Drilling/Machining -> Packaging), generate realistic physical machine telemetry, publish via MQTT, record to CSV files, and visualize on an interactive live Streamlit dashboard.

### 2. Implemented Components
- **Simulation Engine:** `src/simulator/factory_simulator.py`
  - Models RPM, cycle times, queue accumulation, utilization, and machine states.
- **CSV Ingestion:** `src/ingestion/csv_logger.py`
  - Records timestamped telemetry into `data/csv/station01.csv`, `station02.csv`, `station03.csv`, and `production_line.csv`.
- **Streamlit Dashboard:** `dashboard/app.py`
  - Live charts, scenario selection (A through F), Start/Pause/Reset controls.

### 3. How to Run & Verify
```bash
# Execute Layer 1 acceptance test
bash scripts/run_layer1.sh
```

### 4. Acceptance Criteria Checklist
- [x] Three production workstations simulated.
- [x] Machine RPM, cycle time, throughput, queue length, and status calculated.
- [x] MQTT messages published and received.
- [x] CSV files written with valid headers.
- [x] Live Streamlit dashboard operational.

