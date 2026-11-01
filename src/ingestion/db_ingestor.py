"""
FactoryPulse AI - SQLite Ingestion Service
Subscribes to MQTT topics and persists telemetry, alerts, and predictions to SQLite.
"""

import time
import signal
import logging
from typing import Dict, Any

from src.common.config import config
from src.mqtt.client import MQTTClientWrapper
from src.database.db import db
from src.mqtt.broker import broker_manager

logger = logging.getLogger("FactoryPulse.DBIngestor")
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL), format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class DatabaseIngestionService:
    """Consumes telemetry, alert, and prediction messages from MQTT into SQLite."""

    def __init__(self):
        if config.MQTT_MODE == "local":
            broker_manager.ensure_broker_running()

        self.mqtt_client = MQTTClientWrapper(
            client_id_suffix="db_ingestor",
            on_message_callback=self._handle_message,
        )
        self.running = False

    def _handle_message(self, topic: str, payload: Dict[str, Any]):
        try:
            if topic == config.TOPIC_PROCESSED:
                db.insert_production_metric(payload)
            elif "station" in topic and "telemetry" in topic:
                db.insert_sensor_reading(payload)
            elif topic == config.TOPIC_ALERTS:
                db.insert_alert(payload)
            elif topic == config.TOPIC_PREDICTIONS:
                db.insert_prediction(payload)
        except Exception as e:
            logger.error("Failed to ingest message on %s: %s", topic, e)

    def start(self):
        self.mqtt_client.connect(timeout=5.0)
        self.mqtt_client.subscribe(config.TOPIC_STATION1)
        self.mqtt_client.subscribe(config.TOPIC_STATION2)
        self.mqtt_client.subscribe(config.TOPIC_STATION3)
        self.mqtt_client.subscribe(config.TOPIC_PROCESSED)
        self.mqtt_client.subscribe(config.TOPIC_ALERTS)
        self.mqtt_client.subscribe(config.TOPIC_PREDICTIONS)
        self.running = True
        logger.info("Database Ingestion Service active and persisting to SQLite.")

        try:
            while self.running:
                time.sleep(1.0)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False
        self.mqtt_client.disconnect()
        logger.info("Database Ingestion Service stopped.")


if __name__ == "__main__":
    service = DatabaseIngestionService()

    def handle_signal(sig, frame):
        service.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    service.start()

