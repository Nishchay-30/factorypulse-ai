"""
Unit tests for Industrial Alert Engine (hysteresis, debounce, and cooldown).
"""

import pytest
from src.alerts.engine import AlertEngine
from src.database.db import db


def test_alert_engine_hysteresis():
    engine = AlertEngine()
    st_id = "test_station_h"
    engine.base_rpms[st_id] = 1500.0

    # First abnormal reading (< 50 RPM = STOPPED)
    engine.evaluate_station_reading({"station_id": st_id, "rpm": 0.0, "queue_length": 5})
    # Should NOT trigger on 1st reading (requires 3 consecutive readings)
    state = engine._get_state(st_id, "MACHINE_STOPPED")
    assert state["consecutive_abnormal"] == 1
    assert state["is_active"] is False

    # Second abnormal reading
    engine.evaluate_station_reading({"station_id": st_id, "rpm": 0.0, "queue_length": 5})
    assert state["consecutive_abnormal"] == 2
    assert state["is_active"] is False

    # Third abnormal reading -> Should trigger alert!
    engine.evaluate_station_reading({"station_id": st_id, "rpm": 0.0, "queue_length": 5})
    assert state["consecutive_abnormal"] >= 3
    assert state["is_active"] is True


def test_alert_recovery():
    engine = AlertEngine()
    st_id = "test_station_rec"
    engine.base_rpms[st_id] = 1500.0

    # Trigger alert with 3 readings
    for _ in range(3):
        engine.evaluate_station_reading({"station_id": st_id, "rpm": 0.0, "queue_length": 5})
    state = engine._get_state(st_id, "MACHINE_STOPPED")
    assert state["is_active"] is True

    # 3 normal readings to resolve
    for _ in range(3):
        engine.evaluate_station_reading({"station_id": st_id, "rpm": 1500.0, "queue_length": 5})
    assert state["is_active"] is False

