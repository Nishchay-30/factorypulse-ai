"""
FactoryPulse AI - CSV Logger Ingestion Service
Subscribes to MQTT topics and appends structured records to CSV files.
"""

import os
import csv
import logging
import threading
from pathlib import Path
from typing import Dict, Any

from src.common.config import config

logger = logging.getLogger("FactoryPulse.CSVLogger")

STATION_CSV_HEADERS = [
    "timestamp",
    "station_id",
    "station_name",
    "source",
    "rpm",
    "cycle_time",
    "throughput",
    "utilization",
    "queue_length",
    "status",
    "vibration",
    "temperature",
    "current",
]

LINE_CSV_HEADERS = [
    "timestamp",
    "demand_rate",
    "line_throughput",
    "total_wip",
    "bottleneck_station",
    "line_efficiency",
]


class CSVLogger:
    """Manages thread-safe writing of telemetry to disk in CSV format."""

    def __init__(self, output_dir: Path = config.CSV_DATA_DIR):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_files()

    def _init_files(self):
        """Ensure CSV files exist with appropriate headers."""
        with self._lock:
            for station_id in ["station01", "station02", "station03"]:
                csv_path = self.output_dir / f"{station_id}.csv"
                if not csv_path.exists() or csv_path.stat().st_size == 0:
                    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(STATION_CSV_HEADERS)

            line_path = self.output_dir / "production_line.csv"
            if not line_path.exists() or line_path.stat().st_size == 0:
                with open(line_path, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(LINE_CSV_HEADERS)

    def log_station_telemetry(self, data: Dict[str, Any]):
        """Append station telemetry record to station-specific CSV."""
        station_id = data.get("station_id")
        if not station_id:
            return

        csv_path = self.output_dir / f"{station_id}.csv"
        row = [
            data.get("timestamp", ""),
            station_id,
            data.get("station_name", ""),
            data.get("source", "simulated"),
            data.get("rpm", 0.0),
            data.get("cycle_time", 0.0),
            data.get("throughput", 0.0),
            data.get("utilization", 0.0),
            data.get("queue_length", 0),
            data.get("status", "NORMAL"),
            data.get("vibration", ""),
            data.get("temperature", ""),
            data.get("current", ""),
        ]

        with self._lock:
            with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row)

    def log_line_telemetry(self, data: Dict[str, Any]):
        """Append processed line telemetry to production_line.csv."""
        csv_path = self.output_dir / "production_line.csv"
        row = [
            data.get("timestamp", ""),
            data.get("demand_rate", 0.0),
            data.get("line_throughput", 0.0),
            data.get("total_wip", 0),
            data.get("bottleneck_station", ""),
            data.get("line_efficiency", 0.0),
        ]

        with self._lock:
            with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row)

    def on_mqtt_message(self, topic: str, payload: Dict[str, Any]):
        """Handler for incoming MQTT messages."""
        try:
            if "station" in topic:
                self.log_station_telemetry(payload)
            elif "processed" in topic:
                self.log_line_telemetry(payload)
        except Exception as e:
            logger.error("Failed to write CSV record for topic %s: %s", topic, e)


csv_logger = CSVLogger()

