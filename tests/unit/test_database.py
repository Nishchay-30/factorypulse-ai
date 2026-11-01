"""
Unit tests for SQLite Data Access Layer and persistence.
"""

import pytest
import uuid
from src.database.db import db


def test_database_insert_and_deduplication():
    msg_id = str(uuid.uuid4())
    data = {
        "message_id": msg_id,
        "station_id": "station01",
        "source": "simulated",
        "rpm": 1800.0,
        "cycle_time": 3.5,
        "throughput": 17.0,
        "utilization": 0.85,
        "queue_length": 4,
        "status": "NORMAL",
    }
    inserted = db.insert_sensor_reading(data)
    assert inserted is True

    # Duplicate message_id
    duplicate_inserted = db.insert_sensor_reading(data)
    assert duplicate_inserted is False


def test_alert_persistence_and_acknowledgment():
    alert_id = str(uuid.uuid4())
    alert = {
        "alert_id": alert_id,
        "station_id": "station02",
        "severity": "WARNING",
        "alert_code": "RPM_WARNING_LOW",
        "message": "RPM warning",
        "measured_value": 850.0,
        "threshold_value": 1050.0,
    }
    inserted = db.insert_alert(alert)
    assert inserted is True

    # Acknowledge
    ack = db.acknowledge_alert(alert_id, username="admin")
    assert ack is True

    recent = db.get_recent_alerts(limit=10)
    matching = [a for a in recent if a["alert_id"] == alert_id]
    assert len(matching) == 1
    assert matching[0]["acknowledged"] == 1
    assert matching[0]["acknowledged_by"] == "admin"

