# System Architecture Specification
## FactoryPulse AI — Smart Factory Production Bottleneck Prediction

### 1. High-Level Architectural Diagram

```text
                                PHYSICAL LAYER (Layer 6)
                      +------------------------------------------+
                      |   ESP32 DevKit V1 Microcontroller        |
                      |   - LM393 Optical IR Speed Sensor        |
                      |   - L298N Dual H-Bridge Motor Driver     |
                      |   - 12V DC Geared Motor                  |
                      |   - Status LEDs (Green, Yellow, Red)     |
                      |   - Active Warning Buzzer                |
                      +------------------------------------------+
                                    │               ▲
          factory/station02/telemetry│               │ factory/devices/motor01/commands
                                    ▼               │ factory/alerts
+───────────────────────────────────────────────────────────────────────────────────+
|                           SIMULATION ENGINE (Layer 1)                             |
|  - Station 1: Cutting (1800 RPM nominal, 17 PPM capacity)                         |
|  - Station 2: Drilling / Machining (1500 RPM nominal, 15 PPM capacity) [Hybrid]   |
|  - Station 3: Packaging (1200 RPM nominal, 20 PPM capacity)                       |
|  - Material WIP queues, dynamic cycle times, degradation & stoppage scenarios      |
+───────────────────────────────────────────────────────────────────────────────────+
                                    │
                                    ▼
+───────────────────────────────────────────────────────────────────────────────────+
|                     MQTT MESSAGING BROKER LAYER (Layer 2)                         |
|  - Cloud Option: HiveMQ Cloud (TLS 8883, SASL authentication)                     |
|  - Offline / Dev Option: Local Mosquitto Broker (Port 1883)                       |
|  - Resilient In-Process Bus Fallback (Zero external dependency guarantee)         |
+───────────────────────────────────────────────────────────────────────────────────+
                 │                                                │
                 ▼                                                ▼
+───────────────────────────────────+            +───────────────────────────────────+
|     DATA PERSISTENCE (Layer 3)    |            |   AUTOMATION & ALERTS (Layer 4)  |
|  - SQLite (WAL Mode, Concurrency) |            |  - Node-RED Visual Automation Flow|
|  - Message Deduplication          |            |  - Industrial Rule Engine (Debounce|
|  - Schema: readings, metrics,     |            |    hysteresis, alert cooldowns)   |
|    alerts, users, model_metadata  |            |  - Broadcasts to factory/alerts   |
+───────────────────────────────────+            +───────────────────────────────────+
                 │                                                │
                 └───────────────────────┬────────────────────────┘
                                         ▼
+───────────────────────────────────────────────────────────────────────────────────+
|                     AI & MACHINE LEARNING PIPELINE (Layer 5)                      |
|  - Random Forest Classifier (100 estimators, max depth 8, balanced class weights)  |
|  - Strict 60-Second Future Bottleneck Target Window (No Data Leakage)             |
|  - Real-time rolling feature extraction (RPM trend, variability, queue growth)    |
|  - Baseline heuristic comparison & model evaluation metrics                       |
+───────────────────────────────────────────────────────────────────────────────────+
                                         │
                                         ▼
+───────────────────────────────────────────────────────────────────────────────────+
|               FACTORYPULSE AI DASHBOARD & SECURITY (Layer 5)                      |
|  - Streamlit Multi-Page Web Dashboard (10 Specialized Operational Views)          |
|  - Role-Based Authentication (Administrator & Operator accounts via PBKDF2)       |
|  - Live Plotly Telemetry Graphs, Bottleneck Risk Gauge, Scenario Controller        |
+───────────────────────────────────────────────────────────────────────────────────+
```

### 2. Service Separation & Data Flow
1. **Simulation & Hardware Publisher:** Advances workstation states at 1.0s intervals and emits JSON telemetry.
2. **MQTT Broker Layer:** Serves as the central decoupling message bus. Supports QoS 1 delivery and wildcards.
3. **Database Ingestion Engine:** Thread-safe listener storing time-series measurements in SQLite with WAL mode.
4. **Alert Rule Engine:** Evaluates hysteresis counters and issues alerts if abnormal readings persist for 3 consecutive cycles.
5. **Inference Daemon:** Computes 10-second rolling trends and calculates risk probability of a bottleneck within the next 60 seconds.
6. **Frontend Dashboard:** Presents real-time telemetry, model metrics, device controls, and authenticated views.

