"""
Unit tests for Pydantic Telemetry, Alert, and Command schemas.
"""

import pytest
from pydantic import ValidationError
from src.common.schemas import StationTelemetry, AlertMessage, PredictionMessage, MotorCommand


def test_station_telemetry_valid():
    t = StationTelemetry(
        station_id="station01",
        station_name="Cutting",
        source="simulated",
        rpm=1800.0,
        cycle_time=3.5,
        throughput=17.0,
        utilization=0.85,
        queue_length=5,
        status="NORMAL",
    )
    assert t.station_id == "station01"
    assert t.rpm == 1800.0
    assert t.status == "NORMAL"


def test_station_telemetry_invalid_status():
    with pytest.raises(ValidationError):
        StationTelemetry(
            station_id="station01",
            station_name="Cutting",
            rpm=1800.0,
            cycle_time=3.5,
            throughput=17.0,
            utilization=0.85,
            queue_length=5,
            status="INVALID_STATUS_STRING",
        )


def test_alert_message_schema():
    alert = AlertMessage(
        station_id="station02",
        severity="CRITICAL",
        alert_code="MACHINE_STOPPED",
        message="Motor stopped unexpectedly",
        measured_value=0.0,
        threshold_value=50.0,
    )
    assert alert.severity == "CRITICAL"
    assert alert.acknowledged is False


def test_motor_command_schema():
    cmd = MotorCommand(action="SET_SPEED", speed_pwm=200)
    assert cmd.action == "SET_SPEED"
    assert cmd.speed_pwm == 200

    with pytest.raises(ValidationError):
        MotorCommand(action="SET_SPEED", speed_pwm=300)  # Exceeds 255

