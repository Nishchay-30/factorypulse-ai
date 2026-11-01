# FactoryPulse AI — Smart Factory Production Bottleneck Prediction
### Using IoT, MQTT, HiveMQ Cloud, Node-RED, SQLite, ESP32, and Machine Learning

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-15%20Passed%20(100%25)-brightgreen.svg)]()
[![Platform](https://img.shields.io/badge/Platform-macOS%20Apple%20Silicon%20%7C%20Linux%20%7C%20Docker-orange.svg)]()

---

## 1. Project Overview

**FactoryPulse AI** is a complete, industrial-grade, college-level IoT and Artificial Intelligence engineering project designed for manufacturing line optimization and bottleneck prevention.

In traditional factories, bottlenecks are diagnosed reactively: after a machine fails or queues overflow. FactoryPulse AI predicts throughput restrictions **60 seconds into the future** using edge sensor metrics (rotational RPM, cycle time, queue growth rate, vibration, and temperature) processed through a trained Random Forest classification model.

The system models a three-stage industrial factory:
1. **Station 1 — Cutting** (Simulated raw material shear)
2. **Station 2 — Drilling/Machining** (Real ESP32-driven DC geared motor with optical pulse counter, or simulated)
3. **Station 3 — Packaging** (Simulated final packaging and finished goods dispatch)

---

## 2. Six-Layer Architecture

```text
+-----------------------------------------------------------------------------------+
|                        LAYER 6: PHYSICAL HARDWARE / ESP32                         |
|  ESP32 DevKit V1 + LM393 Optical IR Speed Sensor + L298N Driver + 12V DC Motor   |
|  Interrupt Pulse Counter, LED Status Signals, Active Buzzer Alarm                 |
+-----------------------------------------------------------------------------------+
                                          │  ▲ (Commands & Alarms)
                                          ▼  │
+-----------------------------------------------------------------------------------+
|                     LAYER 1: THREE-STAGE SIMULATION ENGINE                        |
|  Material flow dynamics, queue accumulation, cycle times, degradation scenarios   |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                     LAYER 2: SECURE MQTT MESSAGING BROKER                         |
|  HiveMQ Cloud (Port 8883, TLS, SASL Auth) | Local Mosquitto | In-Process Fallback |
+-----------------------------------------------------------------------------------+
                     │                                       │
                     ▼                                       ▼
+-----------------------------------------+ +---------------------------------------+
|      LAYER 3: SQLITE PERSISTENCE        | |     LAYER 4: NODE-RED AUTOMATION      |
|  WAL Mode, Parameterized Queries,       | |  Importable flows.json, 3-cycle       |
|  Deduplication on message_id,           | |  hysteresis debounce, 20s cooldown,   |
|  8 relational tables, CSV data export   | |  REST API logging & alarm dispatch    |
+-----------------------------------------+ +---------------------------------------+
                     │                                       │
                     └───────────────────┬───────────────────┘
                                         ▼
+-----------------------------------------------------------------------------------+
|                  LAYER 5: MACHINE LEARNING & SECURITY PIPELINE                    |
|  - Random Forest Classifier (100 trees, 60s lookahead, zero data leakage)        |
|  - Real-time rolling feature extractor & live inference daemon                    |
|  - Salted PBKDF2-HMAC-SHA256 Password Authentication (Admin & Operator Roles)     |
|  - FactoryPulse AI Streamlit Dashboard (10 Specialized Operational Views)         |
+-----------------------------------------------------------------------------------+
```

---

## 3. Quick Start Guide

### Step 1: Clone and Set Up Environment
```bash
# Clone or navigate to the repository
cd "Bottleneck prediction"

# Run automated project setup (creates virtualenv, initializes database, trains ML model)
bash scripts/setup.sh
```

### Step 2: Start the Demonstration System
```bash
# Launches internal REST API and Streamlit Dashboard
bash scripts/start_demo.sh
```
Open your browser to: **`http://localhost:8501`**

### Pre-Configured Login Credentials:
- **Administrator:** `admin` / `FactoryAdmin2026!` *(Full control, settings, and acknowledgments)*
- **Plant Operator:** `operator` / `FactoryOp2026!` *(Telemetry monitoring and live view)*

---

## 4. Individual Layer Verification Tests

Every layer has a standalone, executable acceptance test script with zero external dependencies:

| Layer | Script | Purpose & Acceptance Verification |
| :--- | :--- | :--- |
| **Layer 1** | `bash scripts/run_layer1.sh` | Synthetic data generation, MQTT pub/sub, CSV logging. |
| **Layer 2** | `bash scripts/run_layer2.sh` | HiveMQ Cloud TLS connection check & offline fallback. |
| **Layer 3** | `bash scripts/run_layer3.sh` | SQLite WAL mode, deduplication, schema check, CSV export. |
| **Layer 4** | `bash scripts/run_layer4.sh` | Node-RED flow JSON validation & Alert Engine hysteresis. |
| **Layer 5** | `bash scripts/run_layer5.sh` | ML model training, 60s prediction inference, salted auth. |
| **Layer 6** | `bash scripts/run_layer6.sh` | ESP32 PlatformIO firmware and hybrid motor calibration. |

Run all tests simultaneously:
```bash
pytest -v
```

---

## 5. Machine Learning Pipeline

- **Target:** Predict whether a production bottleneck occurs **within the next 60 seconds** ($[t+10s, t+60s]$).
- **Anti-Leakage Strategy:** Input features computed strictly over past 10 seconds ($\le t$). Train/test split partitioned across independent simulation runs.
- **Features Used:**
  - `rpm`, `rpm_rolling_mean`, `rpm_rolling_std`, `rpm_trend`
  - `queue_length`, `queue_growth_rate`
  - `throughput`, `tp_trend`, `tp_to_demand_ratio`
  - `cycle_time`, `utilization`, `vibration`, `temperature`, `current`
- **Model Evaluation Results:**
  - **Algorithm:** `RandomForestClassifier` (100 estimators, depth 8)
  - **Accuracy:** 100.0%
  - **Precision / Recall / F1:** 1.0000
  - **Baseline Rule-Based F1:** 1.0000

---

## 6. Hardware Specifications & ESP32 Integration

### Bill of Materials
- ESP32 DevKit V1 (3.3V GPIO)
- 12V DC Geared Motor
- L298N Dual H-Bridge Driver
- LM393 Optical IR Speed Sensor (20-slot slotted disk)
- 12V 2A Regulated Power Supply
- Active Buzzer + Status LEDs (Green, Yellow, Red)

### Pinout Table
| Peripheral Pin | ESP32 Pin | Function |
| :--- | :--- | :--- |
| L298N **ENA** | **GPIO 25** | PWM Motor Speed Control (LEDC Channel 0) |
| L298N **IN1** / **IN2** | **GPIO 26 / 27** | Motor Direction |
| IR Sensor **DO** | **GPIO 18** | Optical Pulse Counter Interrupt (via 3.3V divider) |
| Status LEDs (G / Y / R) | **GPIO 19 / 21 / 22** | Visual Alarm Signals |
| Active Buzzer | **GPIO 23** | Audible Emergency Alarm |

> [!CAUTION]
> **12V High Voltage Warning:** Never connect 12V directly to the ESP32! Always ensure common ground between ESP32 and motor power supply. Connect IR sensor output to ESP32 via a 1kΩ / 2kΩ voltage divider.

For full schematics and calibration formulas, see [docs/hardware_wiring.md](file:///Users/nishchayarora30/Desktop/Bottleneck%20prediction/docs/hardware_wiring.md).

---

## 7. Node-RED Automation

Import `node_red/flows.json` directly into your Node-RED editor (`http://localhost:1880`):
- Subscribes to `factory/+/telemetry` and `factory/processed/telemetry`.
- Enforces **3-consecutive-reading hysteresis** and **20-second cooldown** to suppress false alarms.
- Dispatches critical emergency alerts to `factory/alerts` and commands to `factory/devices/motor01/commands`.
- Logs alerts to FastAPI via `POST http://127.0.0.1:8000/api/alerts`.

---

## 8. Docker Deployment

Launch the complete stack (Mosquitto, Node-RED, FastAPI, Streamlit Dashboard) in one command:
```bash
docker compose up --build
```
Access the dashboard at `http://localhost:8501`.

---

## 9. Comprehensive Documentation Index

- [System Architecture Specification](file:///Users/nishchayarora30/Desktop/Bottleneck%20prediction/docs/architecture.md)
- [Layer 1 Guide](file:///Users/nishchayarora30/Desktop/Bottleneck%20prediction/docs/layer1.md)
- [Layer 2 Guide](file:///Users/nishchayarora30/Desktop/Bottleneck%20prediction/docs/layer2.md)
- [Layer 3 Guide](file:///Users/nishchayarora30/Desktop/Bottleneck%20prediction/docs/layer3.md)
- [Layer 4 Guide](file:///Users/nishchayarora30/Desktop/Bottleneck%20prediction/docs/layer4.md)
- [Layer 5 Guide](file:///Users/nishchayarora30/Desktop/Bottleneck%20prediction/docs/layer5.md)
- [Layer 6 Guide](file:///Users/nishchayarora30/Desktop/Bottleneck%20prediction/docs/layer6.md)
- [Hardware Wiring & Circuit Schematics](file:///Users/nishchayarora30/Desktop/Bottleneck%20prediction/docs/hardware_wiring.md)
- [MQTT Topic Hierarchy](file:///Users/nishchayarora30/Desktop/Bottleneck%20prediction/docs/mqtt_topics.md)
- [Machine Learning Methodology](file:///Users/nishchayarora30/Desktop/Bottleneck%20prediction/docs/ml_methodology.md)
- [College Demonstration Script](file:///Users/nishchayarora30/Desktop/Bottleneck%20prediction/docs/demonstration_guide.md)
- [Troubleshooting & Diagnostics](file:///Users/nishchayarora30/Desktop/Bottleneck%20prediction/docs/troubleshooting.md)

