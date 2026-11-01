# Smart Factory Production Bottleneck Prediction — Task Checklist

## Phase 1: Environment & Project Foundation
- [x] Inspect workspace and prepare virtual environment (`.venv`) <!-- id: 1 -->
- [x] Create core project directories (`config/`, `data/`, `src/`, `dashboard/`, `ml/`, `node_red/`, `firmware/`, `scripts/`, `tests/`, `docs/`) <!-- id: 2 -->
- [x] Write `requirements.txt`, `pyproject.toml`, and `.env.example` <!-- id: 3 -->
- [x] Implement central configuration (`src/common/config.py`) and schemas (`src/common/schemas.py`) <!-- id: 4 -->

## Phase 2: Layer 1 — Synthetic Data → MQTT → CSV → Dashboard
- [x] Implement three-station factory simulator (`src/simulator/factory_simulator.py`) <!-- id: 5 -->
- [x] Implement scenarios A-E (Normal, Gradual Bottleneck, Sudden Stoppage, High Demand, Recovery) <!-- id: 6 -->
- [x] Implement local/offline MQTT broker client & fallback helper (`src/mqtt/broker.py`, `src/mqtt/client.py`) <!-- id: 7 -->
- [x] Implement CSV logger subscriber (`src/ingestion/csv_logger.py`) <!-- id: 8 -->
- [x] Build Layer 1 Streamlit dashboard with real-time graphs, metrics, and scenario controls <!-- id: 9 -->
- [x] Create `scripts/run_layer1.sh` and run acceptance test <!-- id: 10 -->

## Phase 3: Layer 2 — HiveMQ Cloud TLS & Offline Fallback
- [x] Implement TLS connection support (Port 8883, certifi/system CA, username/password auth) <!-- id: 11 -->
- [x] Implement automatic reconnection, QoS handling, buffering, and connection health metrics <!-- id: 12 -->
- [x] Update dashboard with MQTT broker status banner & connection diagnostic panel <!-- id: 13 -->
- [x] Create `scripts/run_layer2.sh` and run acceptance test <!-- id: 14 -->

## Phase 4: Layer 3 — SQLite Persistence & Historical Analytics
- [x] Implement SQLite schema and migration/init (`src/database/schema.sql`, `src/database/db.py`) <!-- id: 15 -->
- [x] Create tables: `machines`, `sensor_readings`, `production_events`, `production_metrics`, `predictions`, `alerts`, `users`, `model_metadata` <!-- id: 16 -->
- [x] Implement single-writer thread-safe ingestion service with WAL mode and deduplication <!-- id: 17 -->
- [x] Implement Historical Analytics queries and CSV export features <!-- id: 18 -->
- [x] Create `scripts/run_layer3.sh` and run acceptance test <!-- id: 19 -->

## Phase 5: Layer 4 — Node-RED Integration & Alert Engine
- [x] Design complete, valid Node-RED flow JSON (`node_red/flows.json`) with FlowFuse Dashboard 2.0 nodes <!-- id: 20 -->
- [x] Implement rule engine with hysteresis, consecutive readings, cooldown, and severity levels (NORMAL, WARNING, CRITICAL) <!-- id: 21 -->
- [x] Implement alert publisher to `factory/alerts` and database logging API <!-- id: 22 -->
- [x] Synchronize dashboard with live alerts and acknowledgment workflow <!-- id: 23 -->
- [x] Create `scripts/run_layer4.sh` and run acceptance test <!-- id: 24 -->

## Phase 6: Layer 5 — AI/ML Bottleneck Prediction & Authentication
- [x] Implement synthetic training dataset generator with 60s future bottleneck horizon (`ml/generate_dataset.py`) <!-- id: 25 -->
- [x] Implement feature engineering and ML training pipeline with Random Forest + baseline (`ml/train.py`) <!-- id: 26 -->
- [x] Implement model evaluation with accuracy, precision, recall, F1, confusion matrix, ROC-AUC (`ml/evaluate.py`) <!-- id: 27 -->
- [x] Implement real-time ML inference service (`src/prediction/predictor.py`) <!-- id: 28 -->
- [x] Implement secure authentication (bcrypt/Argon2 password hashing, session management, roles) (`src/common/auth.py`) <!-- id: 29 -->
- [x] Complete full 10-page Streamlit dashboard (`dashboard/app.py` & pages) <!-- id: 30 -->
- [x] Create `scripts/run_layer5.sh` and run acceptance test <!-- id: 31 -->

## Phase 7: Layer 6 — ESP32 Firmware & Hardware Integration
- [x] Implement complete ESP32 PlatformIO project (`firmware/esp32_motor_station/`) <!-- id: 32 -->
- [x] Implement interrupt-driven IR pulse counting, RPM calculation, L298N PWM speed control, buzzer, and status LEDs <!-- id: 33 -->
- [x] Implement MQTT telemetry publishing (`factory/station02/telemetry`, `factory/devices/motor01/status`) and alert reception (`factory/alerts`, `factory/devices/motor01/commands`) <!-- id: 34 -->
- [x] Implement optional sensor modules (ACS712, MPU6050, DHT11) with null reporting when disconnected <!-- id: 35 -->
- [x] Implement Station 2 hybrid hardware mode (motor RPM calibration -> middle station processing capacity) <!-- id: 36 -->
- [x] Create detailed hardware wiring diagrams, pinout tables, safety notes, and calibration guide (`docs/hardware_wiring.md`) <!-- id: 37 -->
- [x] Create `scripts/run_layer6.sh` and run acceptance test <!-- id: 38 -->

## Phase 8: Testing, Containerization & Complete Documentation
- [x] Write comprehensive unit and integration tests (`tests/`) <!-- id: 39 -->
- [x] Create `docker-compose.yml` for containerized deployment (Mosquitto, Node-RED, Ingestion, Dashboard) <!-- id: 40 -->
- [x] Complete all documentation files (`docs/architecture.md`, `docs/layer1.md` through `docs/layer6.md`, `docs/demonstration_guide.md`, etc.) <!-- id: 41 -->
- [x] Create unified startup and shutdown scripts (`scripts/setup.sh`, `scripts/start_demo.sh`, `scripts/stop_demo.sh`) <!-- id: 42 -->
- [x] Run full test suite and verify all 6 layers and acceptance criteria <!-- id: 43 -->
- [x] Deliver comprehensive final report <!-- id: 44 -->
