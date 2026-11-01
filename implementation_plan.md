# Implementation Plan — FactoryPulse AI
## Smart Factory Production Bottleneck Prediction Using IoT, MQTT, HiveMQ, Node-RED, SQLite, ESP32, and Machine Learning

### 1. Architectural Overview

```text
+-----------------------------------------------------------------------------------+
|                                 PHYSICAL LAYER                                    |
|  ESP32 DevKit + IR Sensor + L298N Motor Driver + 12V DC Motor + LEDs + Buzzer     |
|  (Publishes to factory/station02/telemetry; listens to factory/alerts & commands) |
+-----------------------------------------------------------------------------------+
                                         │  ▲ (Alerts/Commands)
                                         ▼  │
+-----------------------------------------------------------------------------------+
|                             SYNTHETIC SIMULATOR                                   |
|  Station 1 (Cutting) -> Station 2 (Drilling/Machining) -> Station 3 (Packaging)   |
|  Simulates WIP flow, Queues, Cycle Times, RPM, Degradation, Stoppages, & Scenarios|
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                        MQTT BROKER LAYER (PORT 1883 / 8883 TLS)                   |
|  - HiveMQ Cloud (TLS 8883, certifi CA, Username/Password Auth)                    |
|  - Offline Fallback: Local Mosquitto Broker / Embedded Python MQTT Broker Fallback|
+-----------------------------------------------------------------------------------+
                   │                                       │
                   ▼                                       ▼
+-------------------------------------+   +-----------------------------------------+
|     DATA INGESTION & PERSISTENCE    |   |           NODE-RED AUTOMATION           |
|  - Single-writer thread-safe daemon |   |  - Real FlowFuse / Node-RED flows       |
|  - SQLite (WAL mode, parameterized) |   |  - Multi-condition bottleneck detection |
|  - Deduplication & Schema check     |   |  - Hysteresis, cooldown, persistence    |
|  - Tables: machines, readings, etc. |   |  - Publishes to factory/alerts          |
+-------------------------------------+   +-----------------------------------------+
                   │                                       │
                   ▼                                       ▼
+-----------------------------------------------------------------------------------+
|                       AI / ML PREDICTION PIPELINE                                 |
|  - Horizon: Bottleneck predicted within next 60 seconds (no leakage)              |
|  - Features: Rolling RPM, trend, variability, queue growth, throughput vs demand  |
|  - Algorithms: Random Forest Classifier + Rule-based baseline comparison          |
|  - Model evaluation: Accuracy, Precision, Recall, F1, ROC-AUC, Confusion Matrix   |
|  - Real-time inference daemon publishing to factory/predictions                   |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                FACTORYPULSE AI DASHBOARD (STREAMLIT MULTI-PAGE)                   |
|  - Secure Authentication (Argon2 / bcrypt, role-based: admin/operator)           |
|  - 10 Specialized Pages:                                                          |
|    1. Login & Auth Management        6. Alerts & Event Response                   |
|    2. Executive Factory Overview     7. Historical Analytics & CSV Export         |
|    3. Live Real-Time Monitoring      8. AI Model Performance & Metrics            |
|    4. Visual Production Line & Queues9. ESP32 Hardware Device Management          |
|    5. AI Bottleneck Risk Predictions 10. System Settings & Scenarios              |
+-----------------------------------------------------------------------------------+
```

### 2. MQTT Topic Architecture & Schema
- `factory/station01/telemetry`: Cutting station telemetry
- `factory/station02/telemetry`: Drilling/Machining station telemetry (real ESP32 or simulated)
- `factory/station03/telemetry`: Packaging station telemetry
- `factory/processed/telemetry`: Aggregated production-line metrics (throughput, line balance, total WIP)
- `factory/predictions`: Real-time AI prediction results (risk score, bottleneck station, confidence, horizon)
- `factory/alerts`: Threshold and rule-based alerts from Node-RED or Python rule engine
- `factory/devices/motor01/commands`: Remote commands sent to ESP32 (speed PWM, emergency stop, clear alarm)
- `factory/devices/motor01/status`: ESP32 heartbeat, WiFi RSSI, sensor health

### 3. Layer Breakdown and Delivery Strategy
- **Layer 1**: Synthetic three-station generator + MQTT pub/sub + CSV logging + interactive Streamlit dashboard.
- **Layer 2**: HiveMQ Cloud integration with TLS 8883 and seamless local broker fallback.
- **Layer 3**: SQLite schema, WAL mode, thread-safe persistence, historical analytics queries, CSV exports.
- **Layer 4**: Node-RED flows (`flows.json`) with FlowFuse Dashboard nodes, hysteresis, warning/critical severity, and synchronization with backend.
- **Layer 5**: ML pipeline (`generate_dataset.py`, `train.py`, `evaluate.py`, `predictor.py`) + bcrypt authentication + session security.
- **Layer 6**: PlatformIO ESP32 C++ firmware with non-blocking interrupts, L298N PWM control, buzzer/LED alerts, calibration equations, and complete wiring schematics.

### 4. Verification and Acceptance Criteria
Each layer will have an executable verification script (`scripts/run_layerX.sh`) and automated tests (`pytest`) that validate data generation, schema compliance, database persistence, prediction accuracy, and hardware communication compatibility.

