# Layer 4 — MQTT → HiveMQ → SQLite → Node-RED → Dashboard → Alert
## Node-RED Automation Flows, Debounce Hysteresis & Alarm Cooldowns

### 1. Objective
Integrate real importable Node-RED flows and an industrial Alert Rule Engine to evaluate incoming telemetry, detect bottlenecks and slowdowns, enforce debounce hysteresis and alert cooldowns, persist alerts to SQLite, and dispatch physical alarm commands.

### 2. Implemented Components
- **Importable Node-RED Flow:** `node_red/flows.json`
  - MQTT input nodes subscribing to `factory/+/telemetry` and `factory/processed/telemetry`.
  - JavaScript function nodes implementing 3-reading hysteresis and 20-second cooldown.
  - HTTP Request node logging alerts to FastAPI (`POST /api/alerts`).
  - MQTT output node publishing alarms to `factory/alerts` and commands to `factory/devices/motor01/commands`.
- **Node-RED Settings & Packages:** `node_red/settings/settings.js` & `node_red/package.json`.
- **Standalone Alert Engine:** `src/alerts/engine.py`
  - Runs autonomously with or without Node-RED.
  - Generates `NORMAL`, `WARNING`, and `CRITICAL` alerts.
  - Issues resolution events when conditions recover.

### 3. How to Run & Verify
```bash
# Execute Layer 4 acceptance test
bash scripts/run_layer4.sh
```

### 4. Acceptance Criteria Checklist
- [x] Node-RED flow JSON created and syntactically valid.
- [x] Hysteresis confirmation (3 consecutive cycles) prevents false alarms.
- [x] Alert cooldown (20 seconds) prevents message storms.
- [x] Severity levels (NORMAL, WARNING, CRITICAL) enforced.
- [x] Alerts logged to SQLite and dispatched via MQTT.

