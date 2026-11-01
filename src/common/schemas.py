"""
FactoryPulse AI - Data Schemas & Validation
Defines standardized telemetry, alert, prediction, and command schemas.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field, field_validator


def get_utc_timestamp() -> str:
    """Return current ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


class StationTelemetry(BaseModel):
    """Telemetry reading from an individual workstation."""
    schema_version: str = Field(default="1.0.0", description="Schema version")
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=get_utc_timestamp)
    station_id: str = Field(..., description="Unique station ID (station01, station02, station03)")
    station_name: str = Field(..., description="Human readable station name")
    source: str = Field(default="simulated", description="'simulated' or 'hardware'")

    # Operational metrics
    rpm: float = Field(..., ge=0.0, description="Current machine rotational speed (RPM)")
    cycle_time: float = Field(..., ge=0.0, description="Cycle time in seconds")
    throughput: float = Field(..., ge=0.0, description="Throughput in units per minute")
    utilization: float = Field(..., ge=0.0, le=1.0, description="Machine utilization (0.0 to 1.0)")
    queue_length: int = Field(..., ge=0, description="Current queue/WIP upstream buffer")
    status: str = Field(..., description="Machine status: NORMAL, WARNING, CRITICAL, STOPPED, IDLE")

    # Environmental & condition sensors (optional, real or simulated)
    vibration: Optional[float] = Field(default=None, ge=0.0, description="Vibration amplitude (m/s² or mm/s)")
    temperature: Optional[float] = Field(default=None, description="Operating temperature in Celsius")
    current: Optional[float] = Field(default=None, ge=0.0, description="Motor current in Amperes")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = {"NORMAL", "WARNING", "CRITICAL", "STOPPED", "IDLE"}
        if v.upper() not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid_statuses}")
        return v.upper()

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        valid_sources = {"simulated", "hardware"}
        if v.lower() not in valid_sources:
            raise ValueError(f"Invalid source: {v}. Must be 'simulated' or 'hardware'")
        return v.lower()


class ProcessedLineTelemetry(BaseModel):
    """Aggregated factory production-line metrics."""
    schema_version: str = Field(default="1.0.0")
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=get_utc_timestamp)
    demand_rate: float = Field(..., description="Factory target demand rate (units/min)")
    line_throughput: float = Field(..., description="Current exit throughput (Station 3)")
    total_wip: int = Field(..., description="Total work-in-progress units in all queues")
    bottleneck_station: Optional[str] = Field(default=None, description="Identified bottleneck station ID")
    line_efficiency: float = Field(..., ge=0.0, le=1.0, description="Line balance efficiency ratio")
    stations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class AlertMessage(BaseModel):
    """Alert event message."""
    schema_version: str = Field(default="1.0.0")
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=get_utc_timestamp)
    station_id: str = Field(..., description="Originating station ID or 'FACTORY'")
    severity: str = Field(..., description="NORMAL, WARNING, CRITICAL")
    alert_code: str = Field(..., description="E.g., RPM_LOW, QUEUE_OVERFLOW, MACHINE_STOPPED")
    message: str = Field(..., description="Human-readable explanation")
    measured_value: float = Field(..., description="Value that triggered alert")
    threshold_value: float = Field(..., description="Configured limit")
    acknowledged: bool = Field(default=False)
    resolved: bool = Field(default=False)

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        valid = {"NORMAL", "WARNING", "CRITICAL"}
        if v.upper() not in valid:
            raise ValueError(f"Invalid severity: {v}")
        return v.upper()


class PredictionMessage(BaseModel):
    """Machine learning bottleneck prediction output."""
    schema_version: str = Field(default="1.0.0")
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=get_utc_timestamp)
    prediction_horizon_sec: int = Field(default=60)
    bottleneck_predicted: bool = Field(...)
    predicted_station: Optional[str] = Field(default=None)
    risk_probability: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str = Field(default="rf_v1.0")
    features_used: Dict[str, float] = Field(default_factory=dict)


class MotorCommand(BaseModel):
    """Command sent to the physical ESP32 or simulated motor."""
    schema_version: str = Field(default="1.0.0")
    command_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=get_utc_timestamp)
    action: str = Field(..., description="SET_SPEED, START, STOP, RESET_ALARM")
    speed_pwm: Optional[int] = Field(default=None, ge=0, le=255)
    target_rpm: Optional[float] = Field(default=None, ge=0.0)

