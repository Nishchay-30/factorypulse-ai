# Layer 2 — Synthetic Data → MQTT → HiveMQ Cloud → Dashboard
## TLS Encryption, Broker Abstraction & Offline Fallback

### 1. Objective
Establish secure cloud MQTT communication with HiveMQ Cloud on Port 8883 over TLS with username/password authentication, while providing a seamless offline fallback to a local Mosquitto broker or in-process bus.

### 2. Implemented Components
- **MQTT Client Wrapper:** `src/mqtt/client.py`
  - Connects to HiveMQ Cloud with TLS client certificate validation.
  - Automatically reconnects on network interruptions.
  - Switches gracefully to local Mosquitto or In-Process Bus when external connectivity is restricted.
- **Broker Management:** `src/mqtt/broker.py` & `config/mosquitto.conf`
  - Manages local Mosquitto lifecycle on port 1883.
- **Environment Configuration:** `.env.example`
  - Explains all MQTT keys: `MQTT_MODE`, `MQTT_HIVEMQ_HOST`, `MQTT_HIVEMQ_PORT`, `MQTT_HIVEMQ_USERNAME`, `MQTT_HIVEMQ_PASSWORD`, `MQTT_HIVEMQ_USE_TLS`.

### 3. How to Run & Verify
```bash
# Execute Layer 2 acceptance test
bash scripts/run_layer2.sh
```

### 4. Acceptance Criteria Checklist
- [x] HiveMQ Cloud Port 8883 TLS support implemented.
- [x] Auto-reconnect and QoS handling operational.
- [x] Offline fallback guarantees zero crashes when credentials or internet are absent.
- [x] Connection diagnostics displayed on dashboard.

