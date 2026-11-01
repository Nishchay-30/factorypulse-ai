# College Demonstration Script & Presentation Guide
## FactoryPulse AI — Step-by-Step Live Demonstration Guide

This guide provides a structured, professional 10-minute presentation sequence for a final-year engineering college examination or project defense.

---

### Step 1: System Startup & Architecture Introduction (2 Minutes)

1. Open terminal in the project directory:
   ```bash
   bash scripts/start_demo.sh
   ```
2. Explain the high-level engineering motivation to the evaluation panel:
   > *"Good afternoon, members of the committee. FactoryPulse AI is an industrial IoT and Machine Learning system that eliminates factory production bottlenecks before they cause downtime. We model a three-stage manufacturing line: Cutting, Drilling, and Packaging. Unlike traditional systems that detect machine stoppage only after queues have accumulated, FactoryPulse AI predicts throughput restrictions 60 seconds into the future using edge sensors, MQTT, and Random Forest classification."*
3. Open `http://localhost:8501` in your browser.

---

### Step 2: Role-Based Authentication (1 Minute)

1. Show the **Login** screen.
2. Enter Operator credentials: `operator` / `FactoryOp2026!`.
3. Point out role restrictions. Then log in as Administrator: `admin` / `FactoryAdmin2026!`.
4. Explain PBKDF2-HMAC-SHA256 salted password hashing and zero-hardcoded credential architecture.

---

### Step 3: Layer 1–3 Demonstration: Real-Time Flow & Persistence (2 Minutes)

1. Navigate to **Overview** and **Live Monitoring**.
2. Show the three workstations operating under **Scenario A: Normal Factory Operation**.
3. Point out:
   - Station 1 RPM: ~1800, Station 2 RPM: ~1500, Station 3 RPM: ~1200.
   - Queue lengths stable (4–6 units).
   - Line Efficiency: 98–100%.
4. Open SQLite or navigate to **Historical Analytics** and click **Download Station Telemetry (CSV)** to demonstrate live database persistence and CSV export.

---

### Step 4: Layer 4 & 5 Demonstration: Slowdown Scenario & AI Early Warning (3 Minutes)

1. Open the left sidebar and switch Scenario to **Scenario B: Gradual Bottleneck Development**.
2. Navigate to **AI Predictions** and **Live Monitoring**.
3. Observe what happens over the next 45 seconds:
   - Station 2 RPM gradually declines (1500 -> 1200 -> 900 RPM).
   - Input queue for Station 2 starts creeping upward.
   - **Point to the AI Risk Gauge:** Notice the bottleneck probability jumping from 5% to **65%+**.
   - Explain: *"Notice that the machine has not stopped yet, but our trained Random Forest model has already flagged an imminent bottleneck within the 60-second lookahead horizon!"*
4. Once queue crosses 15 units:
   - Point to the **Alerts** page: A **WARNING** alert appears: `station02 upstream queue accumulating`.
   - Explain the **3-cycle hysteresis debounce** and **20-second cooldown** preventing false alarm storms.
   - Click **Acknowledge** to log the operator acknowledgment in the database audit log.

---

### Step 5: Layer 6 Demonstration: Hardware Integration (2 Minutes)

1. Navigate to **Device Management**.
2. If real ESP32 hardware is connected:
   - Point out live IR pulse counting and measured RPM.
   - Use the **PWM Slider** on the dashboard to slow down or speed up the real DC motor.
   - Show how the physical motor's speed directly affects Station 2 throughput in software!
   - Trigger **Emergency Stop** to demonstrate the physical Red LED and Buzzer sounding.
3. If presenting without physical hardware:
   - Switch to **Scenario F: Real ESP32 Hardware Integration**.
   - Show the PlatformIO firmware project structure and `docs/hardware_wiring.md`.
   - Explain how the telemetry protocol seamlessly accepts real hardware measurements.

---

### Step 6: Presentation Conclusion & Q&A Ready Points

- Highlight that all six layers are independent, fully tested with automated pytest suites, and ready for industrial deployment via Docker Compose.
- Invite questions from the evaluators.

