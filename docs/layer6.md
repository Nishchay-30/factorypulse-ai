# Layer 6 — Real Sensors + ESP32 → MQTT → HiveMQ → SQLite → Node-RED → AI/ML → Dashboard → Physical Alerts
## ESP32 DevKit PlatformIO Project, Optical RPM Counting & Physical Feedback

### 1. Objective
Bridge physical hardware into the six-layer software system using an ESP32 DevKit controlling a DC geared motor via an L298N driver, measuring rotational speed with an optical IR pulse counter, and driving status LEDs and an audible buzzer.

### 2. Implemented Components
- **PlatformIO Firmware Project:** `firmware/esp32_motor_station/`
  - `platformio.ini`: Espressif32 platform, Arduino framework, PubSubClient, ArduinoJson.
  - `include/config.h`: GPIO pin definitions, sampling rates, network parameters.
  - `include/sensors.h` & `src/sensors.cpp`: Interrupt-driven pulse counter ISR, LEDC PWM motor drive, status LEDs, buzzer alarm.
  - `src/main.cpp`: Wi-Fi management, MQTT pub/sub, heartbeat telemetry, command execution.
- **Hardware Documentation:** `docs/hardware_wiring.md`
  - Bill of Materials, safety warnings, common-ground rules, voltage dividers, pinout tables, schematic, and calibration math.
- **Hybrid Simulation Mode:** `src/simulator/factory_simulator.py` (Scenario F)
  - Connects real ESP32 motor measurements to Station 2 throughput:  
    $$\text{Throughput} = 15.0 \times \left( \frac{\text{Measured RPM}}{1500} \right)$$

### 3. How to Run & Verify
```bash
# Execute Layer 6 acceptance test
bash scripts/run_layer6.sh
```

### 4. Acceptance Criteria Checklist
- [x] Complete PlatformIO ESP32 firmware project created.
- [x] Interrupt-driven optical pulse counting and RPM calculation implemented.
- [x] Bidirectional MQTT command and alert control implemented.
- [x] Optional sensors (ACS712, MPU6050, DHT11) report explicit null when not installed.
- [x] Detailed wiring tables, circuit diagram, and safety precautions documented.
- [x] Hybrid physical-virtual manufacturing simulation validated.

