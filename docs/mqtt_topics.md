# MQTT Topic Architecture & Message Schemas
## FactoryPulse AI — Industrial Messaging Specification

All MQTT messages use standard versioned JSON payloads (`schema_version: "1.0.0"`).

---

### 1. Topic Hierarchy Overview

| Topic Name | Direction | Frequency | Purpose |
| :--- | :---: | :---: | :--- |
| `factory/station01/telemetry` | Outbound | 1.0s | Station 1 (Cutting) live telemetry |
| `factory/station02/telemetry` | Outbound | 1.0s | Station 2 (Drilling / ESP32) live telemetry |
| `factory/station03/telemetry` | Outbound | 1.0s | Station 3 (Packaging) live telemetry |
| `factory/processed/telemetry` | Outbound | 1.0s | Factory-wide aggregated line KPIs |
| `factory/predictions` | Outbound | Event/1.0s | Real-time AI bottleneck risk forecasts |
| `factory/alerts` | Bidirectional | Event-based | Industrial threshold warnings & critical alarms |
| `factory/devices/motor01/commands` | Inbound to ESP32 | On demand | Remote actuator & speed commands |
| `factory/devices/motor01/status` | Outbound | 5.0s | ESP32 hardware heartbeat & telemetry |

---

### 2. Message Payload Schemas

#### A. Station Telemetry (`factory/+/telemetry`)
```json
{
  "schema_version": "1.0.0",
  "message_id": "c1f7b99c-e4bb-4e9e-990a-5c1eb02c4232",
  "timestamp": "2026-10-29T10:15:30.123456+00:00",
  "station_id": "station02",
  "station_name": "Drilling/Machining",
  "source": "simulated",
  "rpm": 1492.4,
  "cycle_time": 4.02,
  "throughput": 14.92,
  "utilization": 0.865,
  "queue_length": 6,
  "status": "NORMAL",
  "vibration": 1.25,
  "temperature": 36.8,
  "current": 0.86
}
```

#### B. Aggregated Line Telemetry (`factory/processed/telemetry`)
```json
{
  "schema_version": "1.0.0",
  "message_id": "8f8b65e1-8894-4d8e-99ba-3dc84cbcf999",
  "timestamp": "2026-10-29T10:15:30.123456+00:00",
  "demand_rate": 15.0,
  "line_throughput": 14.85,
  "total_wip": 16,
  "bottleneck_station": null,
  "line_efficiency": 0.990,
  "stations": {
    "station01": { ... },
    "station02": { ... },
    "station03": { ... }
  }
}
```

#### C. AI Bottleneck Prediction (`factory/predictions`)
```json
{
  "schema_version": "1.0.0",
  "prediction_id": "a90123cd-9182-4f11-9ab0-112233445566",
  "timestamp": "2026-10-29T10:15:30.200000+00:00",
  "prediction_horizon_sec": 60,
  "bottleneck_predicted": true,
  "predicted_station": "station02",
  "risk_probability": 0.745,
  "confidence": 0.880,
  "model_version": "rf_v1.0",
  "features_used": {
    "rpm": 1120.5,
    "queue_length": 14,
    "rpm_rolling_mean": 1280.4,
    "rpm_trend": -12.5,
    "queue_growth_rate": 0.8
  }
}
```

#### D. Industrial Alert Event (`factory/alerts`)
```json
{
  "schema_version": "1.0.0",
  "alert_id": "4e12c09d-00ab-48f1-8ac1-9876543210ab",
  "timestamp": "2026-10-29T10:15:32.000000+00:00",
  "station_id": "station02",
  "severity": "WARNING",
  "alert_code": "QUEUE_WARNING_HIGH",
  "message": "station02 upstream queue accumulating (16 units >= 15)",
  "measured_value": 16.0,
  "threshold_value": 15.0,
  "acknowledged": false,
  "resolved": false
}
```

#### E. Motor Control Command (`factory/devices/motor01/commands`)
```json
{
  "schema_version": "1.0.0",
  "command_id": "cmd_1793268900",
  "timestamp": "2026-10-29T10:15:35.000000+00:00",
  "action": "SET_SPEED",
  "speed_pwm": 180,
  "target_rpm": 1250.0
}
```

