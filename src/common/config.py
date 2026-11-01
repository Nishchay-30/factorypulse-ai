"""
FactoryPulse AI - Central Configuration Module
Provides strongly typed access to environment variables and system defaults.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class AppConfig:
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PROJECT_ROOT: Path = PROJECT_ROOT

    # MQTT Settings
    MQTT_MODE: str = os.getenv("MQTT_MODE", "local").lower()  # "hivemq" or "local"
    MQTT_LOCAL_HOST: str = os.getenv("MQTT_LOCAL_HOST", "127.0.0.1")
    MQTT_LOCAL_PORT: int = int(os.getenv("MQTT_LOCAL_PORT", "1883"))
    MQTT_LOCAL_KEEPALIVE: int = int(os.getenv("MQTT_LOCAL_KEEPALIVE", "60"))

    # HiveMQ Cloud
    MQTT_HIVEMQ_HOST: str = os.getenv("MQTT_HIVEMQ_HOST", "")
    MQTT_HIVEMQ_PORT: int = int(os.getenv("MQTT_HIVEMQ_PORT", "8883"))
    MQTT_HIVEMQ_USERNAME: str = os.getenv("MQTT_HIVEMQ_USERNAME", "")
    MQTT_HIVEMQ_PASSWORD: str = os.getenv("MQTT_HIVEMQ_PASSWORD", "")
    MQTT_HIVEMQ_USE_TLS: bool = os.getenv("MQTT_HIVEMQ_USE_TLS", "true").lower() == "true"

    # MQTT Topics
    MQTT_CLIENT_ID_PREFIX: str = os.getenv("MQTT_CLIENT_ID_PREFIX", "factorypulse_")
    TOPIC_STATION1: str = os.getenv("MQTT_TOPIC_STATION1", "factory/station01/telemetry")
    TOPIC_STATION2: str = os.getenv("MQTT_TOPIC_STATION2", "factory/station02/telemetry")
    TOPIC_STATION3: str = os.getenv("MQTT_TOPIC_STATION3", "factory/station03/telemetry")
    TOPIC_PROCESSED: str = os.getenv("MQTT_TOPIC_PROCESSED", "factory/processed/telemetry")
    TOPIC_PREDICTIONS: str = os.getenv("MQTT_TOPIC_PREDICTIONS", "factory/predictions")
    TOPIC_ALERTS: str = os.getenv("MQTT_TOPIC_ALERTS", "factory/alerts")
    TOPIC_MOTOR_COMMANDS: str = os.getenv("MQTT_TOPIC_MOTOR_COMMANDS", "factory/devices/motor01/commands")
    TOPIC_MOTOR_STATUS: str = os.getenv("MQTT_TOPIC_MOTOR_STATUS", "factory/devices/motor01/status")

    # Database
    DATABASE_PATH: Path = PROJECT_ROOT / os.getenv("DATABASE_PATH", "data/database/factorypulse.db")
    DATABASE_WAL_MODE: bool = os.getenv("DATABASE_WAL_MODE", "true").lower() == "true"
    DATABASE_TIMEOUT: float = float(os.getenv("DATABASE_TIMEOUT", "15.0"))
    CSV_DATA_DIR: Path = PROJECT_ROOT / "data" / "csv"

    # Simulation Settings
    SIMULATION_INTERVAL_SEC: float = float(os.getenv("SIMULATION_INTERVAL_SEC", "1.0"))
    SIMULATION_TIME_SCALE: float = float(os.getenv("SIMULATION_TIME_SCALE", "1.0"))
    DEFAULT_SCENARIO: str = os.getenv("DEFAULT_SCENARIO", "scenario_a")
    STATION2_MODE: str = os.getenv("STATION2_MODE", "simulated")  # "simulated" or "hardware"

    DEMAND_RATE_UNITS_PER_MIN: float = float(os.getenv("DEMAND_RATE_UNITS_PER_MIN", "15.0"))
    MAX_QUEUE_CAPACITY: int = int(os.getenv("MAX_QUEUE_CAPACITY", "50"))

    # Station Baselines
    STATION1_BASE_RPM: float = float(os.getenv("STATION1_BASE_RPM", "1800.0"))
    STATION1_CYCLE_TIME_SEC: float = float(os.getenv("STATION1_CYCLE_TIME_SEC", "3.5"))
    STATION1_CAPACITY_PER_MIN: float = float(os.getenv("STATION1_CAPACITY_PER_MIN", "17.0"))

    STATION2_BASE_RPM: float = float(os.getenv("STATION2_BASE_RPM", "1500.0"))
    STATION2_CYCLE_TIME_SEC: float = float(os.getenv("STATION2_CYCLE_TIME_SEC", "4.0"))
    STATION2_CAPACITY_PER_MIN: float = float(os.getenv("STATION2_CAPACITY_PER_MIN", "15.0"))

    STATION3_BASE_RPM: float = float(os.getenv("STATION3_BASE_RPM", "1200.0"))
    STATION3_CYCLE_TIME_SEC: float = float(os.getenv("STATION3_CYCLE_TIME_SEC", "3.0"))
    STATION3_CAPACITY_PER_MIN: float = float(os.getenv("STATION3_CAPACITY_PER_MIN", "20.0"))

    # Alert Thresholds
    ALERT_RPM_CRITICAL_RATIO: float = float(os.getenv("ALERT_RPM_CRITICAL_RATIO", "0.40"))
    ALERT_RPM_WARNING_RATIO: float = float(os.getenv("ALERT_RPM_WARNING_RATIO", "0.70"))
    ALERT_QUEUE_WARNING_THRESHOLD: int = int(os.getenv("ALERT_QUEUE_WARNING_THRESHOLD", "15"))
    ALERT_QUEUE_CRITICAL_THRESHOLD: int = int(os.getenv("ALERT_QUEUE_CRITICAL_THRESHOLD", "30"))
    ALERT_HYSTERESIS_COUNT: int = int(os.getenv("ALERT_HYSTERESIS_COUNT", "3"))
    ALERT_COOLDOWN_SECONDS: int = int(os.getenv("ALERT_COOLDOWN_SECONDS", "20"))

    # Machine Learning
    ML_MODEL_PATH: Path = PROJECT_ROOT / os.getenv("ML_MODEL_PATH", "ml/models/bottleneck_rf_model.joblib")
    ML_METADATA_PATH: Path = PROJECT_ROOT / os.getenv("ML_METADATA_PATH", "ml/models/model_metadata.json")
    ML_PREDICTION_HORIZON_SEC: int = int(os.getenv("ML_PREDICTION_HORIZON_SEC", "60"))
    ML_ROLLING_WINDOW_SIZE: int = int(os.getenv("ML_ROLLING_WINDOW_SIZE", "10"))

    # Authentication & Security
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_INITIAL_PASSWORD: str = os.getenv("ADMIN_INITIAL_PASSWORD", "FactoryAdmin2026!")
    OPERATOR_USERNAME: str = os.getenv("OPERATOR_USERNAME", "operator")
    OPERATOR_INITIAL_PASSWORD: str = os.getenv("OPERATOR_INITIAL_PASSWORD", "FactoryOp2026!")
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "factorypulse_super_secret_key_2026")


config = AppConfig()

