"""
FactoryPulse AI - Telemetry Ingestion Subscriber Daemon
Listens on MQTT topics and routes messages to CSV files.
"""

import time
import signal
import logging
from typing import Dict, Any

from src.common.config import config
from src.mqtt.client import MQTTClientWrapper
from src.ingestion.csv_logger import csv_logger
from src.mqtt.broker import broker_manager

logger = logging.getLogger("FactoryPulse.IngestionSubscriber")
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL), format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class IngestionSubscriber:
    """Manages telemetry ingestion from MQTT to CSV storage."""

    def __init__(self):
        if config.MQTT_MODE == "local":
            broker_manager.ensure_broker_running()

        self.mqtt_client = MQTTClientWrapper(
            client_id_suffix="csv_ingestion",
            on_message_callback=self._handle_message,
        )
        self.running = False

    def _handle_message(self, topic: str, payload: Dict[str, Any]):
        csv_logger.on_mqtt_message(topic, payload)

    def start(self):
        self.mqtt_client.connect(timeout=5.0)
        # Subscribe to all telemetry topics
        self.mqtt_client.subscribe(config.TOPIC_STATION1)
        self.mqtt_client.subscribe(config.TOPIC_STATION2)
        self.mqtt_client.subscribe(config.TOPIC_STATION3)
        self.mqtt_client.subscribe(config.TOPIC_PROCESSED)
        self.running = True
        logger.info("CSV Ingestion subscriber active and logging.")

        try:
            while self.running:
                time.sleep(1.0)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False
        self.mqtt_client.disconnect()
        logger.info("CSV Ingestion subscriber stopped.")


if __name__ == "__main__":
    subscriber = IngestionSubscriber()

    def handle_signal(sig, frame):
        subscriber.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    subscriber.start()

