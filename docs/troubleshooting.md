# Troubleshooting & Diagnostic Guide
## FactoryPulse AI — Common Issues and Solutions

### 1. MQTT Connection Issues

#### Problem: MQTT Client cannot connect to local broker (`Connection refused` or `Address already in use`)
- **Cause:** No MQTT broker is running, or another process is occupying Port 1883.
- **Solution:**
  1. Check if Mosquitto is running: `lsof -i :1883` or `ps aux | grep mosquitto`.
  2. Start Mosquitto using the project configuration:
     ```bash
     /opt/homebrew/sbin/mosquitto -c config/mosquitto.conf
     ```
  3. Alternatively, FactoryPulse AI automatically activates its **In-Process Message Bus Fallback**, allowing full local execution without external network sockets!

#### Problem: HiveMQ Cloud TLS fails with certificate error
- **Cause:** CA certificate validation failed, or credentials in `.env` are invalid.
- **Solution:**
  1. Confirm your HiveMQ Cloud cluster URL ends in `.s1.eu.hivemq.cloud` or similar.
  2. Confirm `MQTT_HIVEMQ_PORT=8883`.
  3. Set `MQTT_MODE=local` in `.env` if internet access or credentials are not yet available.

---

### 2. Machine Learning & Prediction Issues

#### Problem: Dashboard shows "Model unavailable" or "rules_fallback"
- **Cause:** Model has not been trained or artifact file is missing.
- **Solution:**
  1. Run the training script:
     ```bash
     source .venv/bin/activate
     python3 ml/generate_dataset.py
     python3 ml/train.py
     ```
  2. Verify artifact exists at `ml/models/bottleneck_rf_model.joblib`.

---

### 3. ESP32 Hardware Issues

#### Problem: ESP32 reads 0 RPM even when motor is spinning
- **Cause:** IR speed sensor beam is misaligned, optical disk slots are not passing through sensor gap, or missing common ground.
- **Solution:**
  1. Ensure the slotted encoder wheel rotates cleanly inside the optical slot without rubbing.
  2. Verify sensor LED flickers as slots pass through the infrared beam.
  3. Ensure common ground between ESP32 and motor power supply.
  4. Ensure IR sensor `DO` pin is connected to **GPIO 18** via 3.3V voltage divider.

#### Problem: Motor does not spin when commanded
- **Cause:** L298N 12V power supply disconnected, ENA jumper missing without PWM, or IN1/IN2 both LOW.
- **Solution:**
  1. Check 12V power supply to L298N VMS terminal.
  2. Ensure ESP32 **GPIO 25** is connected to L298N **ENA** (remove default jumper on ENA pin).
  3. Check Serial Monitor output at 115200 baud for received commands.

