"""
FactoryPulse AI - SQLite Database Access Layer (DAL)
Thread-safe connection handling, WAL mode, schema initialization, and parameterized queries.
"""

import sqlite3
import logging
import threading
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from src.common.config import config
from src.common.schemas import StationTelemetry, ProcessedLineTelemetry, AlertMessage, PredictionMessage

logger = logging.getLogger("FactoryPulse.Database")


class DatabaseManager:
    """Thread-safe SQLite manager with WAL mode and dedicated writer synchronization."""

    def __init__(self, db_path: Path = config.DATABASE_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.Lock()
        self._local = threading.local()
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection with WAL mode and foreign keys enabled."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=config.DATABASE_TIMEOUT,
                check_same_thread=False,
            )
            conn.row_factory = sqlite3.Row
            # Enable WAL mode for high concurrency
            if config.DATABASE_WAL_MODE:
                conn.execute("PRAGMA journal_mode = WAL;")
                conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            self._local.conn = conn
        return self._local.conn

    def init_db(self):
        """Execute schema creation and seed baseline machines."""
        schema_path = config.PROJECT_ROOT / "src" / "database" / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found at {schema_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        with self._write_lock:
            conn = self.get_connection()
            with conn:
                conn.executescript(schema_sql)
            self._seed_machines(conn)
            logger.info("Database initialized successfully at %s", self.db_path)

    def _seed_machines(self, conn: sqlite3.Connection):
        """Seed baseline factory workstation records."""
        machines = [
            ("station01", "Cutting Station", "Mechanical Shear", config.STATION1_BASE_RPM, config.STATION1_CAPACITY_PER_MIN, "simulated"),
            ("station02", "Drilling Station", "CNC Drill / Motor", config.STATION2_BASE_RPM, config.STATION2_CAPACITY_PER_MIN, "simulated"),
            ("station03", "Packaging Station", "Automated Packer", config.STATION3_BASE_RPM, config.STATION3_CAPACITY_PER_MIN, "simulated"),
        ]
        with conn:
            for m in machines:
                conn.execute(
                    """
                    INSERT INTO machines (station_id, name, type, base_rpm, nominal_capacity, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(station_id) DO UPDATE SET
                        base_rpm=excluded.base_rpm,
                        nominal_capacity=excluded.nominal_capacity;
                    """,
                    m,
                )

    # --------------------------------------------------------------------------
    # Telemetry Operations
    # --------------------------------------------------------------------------
    def insert_sensor_reading(self, reading: Dict[str, Any]) -> bool:
        """Insert a workstation sensor reading (deduplicates on message_id)."""
        sql = """
        INSERT INTO sensor_readings (
            message_id, timestamp, station_id, source, rpm, cycle_time,
            throughput, utilization, queue_length, status, vibration,
            temperature, current
        ) VALUES (
            :message_id, :timestamp, :station_id, :source, :rpm, :cycle_time,
            :throughput, :utilization, :queue_length, :status, :vibration,
            :temperature, :current
        ) ON CONFLICT(message_id) DO NOTHING;
        """
        params = {
            "message_id": reading.get("message_id", str(datetime.now(timezone.utc).timestamp())),
            "timestamp": reading.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "station_id": reading.get("station_id"),
            "source": reading.get("source", "simulated"),
            "rpm": float(reading.get("rpm", 0.0)),
            "cycle_time": float(reading.get("cycle_time", 0.0)),
            "throughput": float(reading.get("throughput", 0.0)),
            "utilization": float(reading.get("utilization", 0.0)),
            "queue_length": int(reading.get("queue_length", 0)),
            "status": reading.get("status", "NORMAL"),
            "vibration": reading.get("vibration"),
            "temperature": reading.get("temperature"),
            "current": reading.get("current"),
        }
        with self._write_lock:
            conn = self.get_connection()
            with conn:
                cursor = conn.execute(sql, params)
                return cursor.rowcount > 0

    def insert_production_metric(self, metric: Dict[str, Any]) -> bool:
        """Insert aggregated line telemetry metric."""
        sql = """
        INSERT INTO production_metrics (
            message_id, timestamp, demand_rate, line_throughput,
            total_wip, bottleneck_station, line_efficiency
        ) VALUES (
            :message_id, :timestamp, :demand_rate, :line_throughput,
            :total_wip, :bottleneck_station, :line_efficiency
        ) ON CONFLICT(message_id) DO NOTHING;
        """
        params = {
            "message_id": metric.get("message_id", str(datetime.now(timezone.utc).timestamp())),
            "timestamp": metric.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "demand_rate": float(metric.get("demand_rate", 0.0)),
            "line_throughput": float(metric.get("line_throughput", 0.0)),
            "total_wip": int(metric.get("total_wip", 0)),
            "bottleneck_station": metric.get("bottleneck_station"),
            "line_efficiency": float(metric.get("line_efficiency", 0.0)),
        }
        with self._write_lock:
            conn = self.get_connection()
            with conn:
                cursor = conn.execute(sql, params)
                return cursor.rowcount > 0

    def insert_event(self, event_id: str, event_type: str, description: str, station_id: Optional[str] = None, details: Optional[Dict] = None):
        """Record a production event."""
        sql = """
        INSERT INTO production_events (event_id, timestamp, station_id, event_type, description, details_json)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(event_id) DO NOTHING;
        """
        with self._write_lock:
            conn = self.get_connection()
            with conn:
                conn.execute(sql, (
                    event_id,
                    datetime.now(timezone.utc).isoformat(),
                    station_id,
                    event_type,
                    description,
                    json.dumps(details or {}),
                ))

    # --------------------------------------------------------------------------
    # Alerts Operations
    # --------------------------------------------------------------------------
    def insert_alert(self, alert: Dict[str, Any]) -> bool:
        """Insert an operational alert."""
        sql = """
        INSERT INTO alerts (
            alert_id, timestamp, station_id, severity, alert_code,
            message, measured_value, threshold_value, acknowledged, resolved
        ) VALUES (
            :alert_id, :timestamp, :station_id, :severity, :alert_code,
            :message, :measured_value, :threshold_value, :acknowledged, :resolved
        ) ON CONFLICT(alert_id) DO NOTHING;
        """
        params = {
            "alert_id": alert.get("alert_id"),
            "timestamp": alert.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "station_id": alert.get("station_id"),
            "severity": alert.get("severity", "WARNING"),
            "alert_code": alert.get("alert_code", "UNKNOWN"),
            "message": alert.get("message", ""),
            "measured_value": float(alert.get("measured_value", 0.0)),
            "threshold_value": float(alert.get("threshold_value", 0.0)),
            "acknowledged": 1 if alert.get("acknowledged") else 0,
            "resolved": 1 if alert.get("resolved") else 0,
        }
        with self._write_lock:
            conn = self.get_connection()
            with conn:
                cursor = conn.execute(sql, params)
                return cursor.rowcount > 0

    def acknowledge_alert(self, alert_id: str, username: str) -> bool:
        """Acknowledge an active alert."""
        sql = """
        UPDATE alerts
        SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = ?
        WHERE alert_id = ?;
        """
        with self._write_lock:
            conn = self.get_connection()
            with conn:
                cursor = conn.execute(sql, (username, datetime.now(timezone.utc).isoformat(), alert_id))
                return cursor.rowcount > 0

    def get_recent_alerts(self, limit: int = 50, unacknowledged_only: bool = False) -> List[Dict[str, Any]]:
        """Retrieve recent alerts."""
        conn = self.get_connection()
        if unacknowledged_only:
            query = "SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY timestamp DESC LIMIT ?;"
        else:
            query = "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?;"
        cursor = conn.execute(query, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    # --------------------------------------------------------------------------
    # AI Predictions Operations
    # --------------------------------------------------------------------------
    def insert_prediction(self, pred: Dict[str, Any]) -> bool:
        """Insert ML bottleneck prediction record."""
        sql = """
        INSERT INTO predictions (
            prediction_id, timestamp, horizon_sec, bottleneck_predicted,
            predicted_station, risk_probability, confidence, model_version, features_json
        ) VALUES (
            :prediction_id, :timestamp, :horizon_sec, :bottleneck_predicted,
            :predicted_station, :risk_probability, :confidence, :model_version, :features_json
        ) ON CONFLICT(prediction_id) DO NOTHING;
        """
        params = {
            "prediction_id": pred.get("prediction_id"),
            "timestamp": pred.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "horizon_sec": int(pred.get("prediction_horizon_sec", pred.get("horizon_sec", 60))),
            "bottleneck_predicted": 1 if pred.get("bottleneck_predicted") else 0,
            "predicted_station": pred.get("predicted_station"),
            "risk_probability": float(pred.get("risk_probability", 0.0)),
            "confidence": float(pred.get("confidence", 0.0)),
            "model_version": pred.get("model_version", "v1.0"),
            "features_json": json.dumps(pred.get("features_used", {})),
        }
        with self._write_lock:
            conn = self.get_connection()
            with conn:
                cursor = conn.execute(sql, params)
                return cursor.rowcount > 0

    def get_recent_predictions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent AI predictions."""
        conn = self.get_connection()
        cursor = conn.execute("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT ?;", (limit,))
        return [dict(row) for row in cursor.fetchall()]

    # --------------------------------------------------------------------------
    # Analytics & Querying
    # --------------------------------------------------------------------------
    def get_recent_readings(self, station_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent sensor readings ordered chronologically."""
        conn = self.get_connection()
        if station_id:
            query = """
            SELECT * FROM (
                SELECT * FROM sensor_readings
                WHERE station_id = ?
                ORDER BY timestamp DESC LIMIT ?
            ) ORDER BY timestamp ASC;
            """
            cursor = conn.execute(query, (station_id, limit))
        else:
            query = """
            SELECT * FROM (
                SELECT * FROM sensor_readings
                ORDER BY timestamp DESC LIMIT ?
            ) ORDER BY timestamp ASC;
            """
            cursor = conn.execute(query, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_recent_line_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve recent line-level production metrics ordered chronologically."""
        conn = self.get_connection()
        query = """
        SELECT * FROM (
            SELECT * FROM production_metrics
            ORDER BY timestamp DESC LIMIT ?
        ) ORDER BY timestamp ASC;
        """
        cursor = conn.execute(query, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_station_summary(self, station_id: str) -> Optional[Dict[str, Any]]:
        """Compute aggregated statistics for a specific workstation."""
        conn = self.get_connection()
        query = """
        SELECT
            station_id,
            COUNT(*) as total_samples,
            AVG(rpm) as avg_rpm,
            MAX(rpm) as max_rpm,
            MIN(rpm) as min_rpm,
            AVG(throughput) as avg_throughput,
            AVG(queue_length) as avg_queue,
            MAX(queue_length) as max_queue,
            AVG(utilization) as avg_utilization
        FROM sensor_readings
        WHERE station_id = ?;
        """
        cursor = conn.execute(query, (station_id,))
        row = cursor.fetchone()
        return dict(row) if row and row["total_samples"] > 0 else None

    # --------------------------------------------------------------------------
    # Model Metadata Operations
    # --------------------------------------------------------------------------
    def save_model_metadata(self, meta: Dict[str, Any]):
        """Persist ML model evaluation metrics and hyperparameters."""
        sql = """
        INSERT INTO model_metadata (
            model_version, algorithm, trained_at, accuracy, precision,
            recall, f1_score, roc_auc, parameters_json, is_active
        ) VALUES (
            :model_version, :algorithm, :trained_at, :accuracy, :precision,
            :recall, :f1_score, :roc_auc, :parameters_json, 1
        ) ON CONFLICT(model_version) DO UPDATE SET
            accuracy=excluded.accuracy,
            precision=excluded.precision,
            recall=excluded.recall,
            f1_score=excluded.f1_score,
            roc_auc=excluded.roc_auc,
            parameters_json=excluded.parameters_json;
        """
        params = {
            "model_version": meta.get("model_version"),
            "algorithm": meta.get("algorithm", "RandomForestClassifier"),
            "trained_at": meta.get("trained_at", datetime.now(timezone.utc).isoformat()),
            "accuracy": float(meta.get("accuracy", 0.0)),
            "precision": float(meta.get("precision", 0.0)),
            "recall": float(meta.get("recall", 0.0)),
            "f1_score": float(meta.get("f1_score", 0.0)),
            "roc_auc": float(meta.get("roc_auc")) if meta.get("roc_auc") is not None else None,
            "parameters_json": json.dumps(meta.get("parameters", {})),
        }
        with self._write_lock:
            conn = self.get_connection()
            with conn:
                conn.execute(sql, params)

    def get_active_model_metadata(self) -> Optional[Dict[str, Any]]:
        """Retrieve metadata of the currently active ML model."""
        conn = self.get_connection()
        cursor = conn.execute("SELECT * FROM model_metadata WHERE is_active = 1 ORDER BY id DESC LIMIT 1;")
        row = cursor.fetchone()
        return dict(row) if row else None


db = DatabaseManager()

