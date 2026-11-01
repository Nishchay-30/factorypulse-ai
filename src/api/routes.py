"""
FactoryPulse AI - FastAPI Internal Backend REST API
Provides endpoints for Node-RED, external integrations, alerts, and metrics.
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any

from src.common.schemas import AlertMessage, MotorCommand, StationTelemetry, ProcessedLineTelemetry
from src.database.db import db
from src.mqtt.client import MQTTClientWrapper
from src.common.config import config

api_app = FastAPI(
    title="FactoryPulse AI Internal API",
    version="1.0.0",
    description="REST API for Smart Factory Bottleneck Prediction, Node-RED integration, and Alerts",
)

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mqtt_client = MQTTClientWrapper(client_id_suffix="rest_api")


@api_app.on_event("startup")
def startup_event():
    mqtt_client.connect(timeout=2.0)


@api_app.on_event("shutdown")
def shutdown_event():
    mqtt_client.disconnect()


@api_app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "mqtt_connected": mqtt_client.is_connected,
        "mqtt_mode": mqtt_client.connection_info.get("mode"),
    }


@api_app.post("/api/alerts")
def create_alert(alert: AlertMessage):
    """Receive alert from Node-RED or external service, persist to SQLite and broadcast via MQTT."""
    success = db.insert_alert(alert.model_dump())
    # Publish to MQTT topic
    mqtt_client.publish(config.TOPIC_ALERTS, alert.model_dump())
    return {"status": "recorded", "alert_id": alert.alert_id, "persisted": success}


@api_app.get("/api/alerts")
def get_alerts(limit: int = 50, unacknowledged: bool = False):
    """Retrieve recent alerts."""
    return db.get_recent_alerts(limit=limit, unacknowledged_only=unacknowledged)


@api_app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, username: str = Query("operator")):
    """Acknowledge an alert."""
    updated = db.acknowledge_alert(alert_id, username)
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found or already acknowledged")
    return {"status": "acknowledged", "alert_id": alert_id, "by": username}


@api_app.post("/api/commands/motor")
def send_motor_command(command: MotorCommand):
    """Publish remote command to physical ESP32 or simulated workstation."""
    published = mqtt_client.publish(config.TOPIC_MOTOR_COMMANDS, command.model_dump())
    return {"status": "dispatched", "command_id": command.command_id, "published": published}


@api_app.get("/api/telemetry/recent")
def get_recent_telemetry(station_id: Optional[str] = None, limit: int = 50):
    """Query recent telemetry readings."""
    return db.get_recent_readings(station_id=station_id, limit=limit)

