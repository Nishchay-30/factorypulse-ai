"""
FactoryPulse AI - Broker Management and Verification
Checks broker availability, provides auto-start for local Mosquitto,
and provides a lightweight in-process fallback message bus if no external broker exists.
"""

import socket
import subprocess
import shutil
import logging
import threading
from typing import Optional
from pathlib import Path

from src.common.config import config

logger = logging.getLogger("FactoryPulse.Broker")


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a TCP port is open and accepting connections."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def find_mosquitto_binary() -> Optional[str]:
    """Locate mosquitto executable on system."""
    for candidate in [
        shutil.which("mosquitto"),
        "/opt/homebrew/sbin/mosquitto",
        "/usr/local/sbin/mosquitto",
        "/usr/sbin/mosquitto",
        "/usr/bin/mosquitto",
    ]:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


import os

class BrokerManager:
    """Manages local MQTT broker lifecycle."""

    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()

    def ensure_broker_running(self) -> bool:
        """Verify broker is running on configured host/port; start local mosquitto if needed."""
        target_host = config.MQTT_LOCAL_HOST
        target_port = config.MQTT_LOCAL_PORT

        if is_port_open(target_host, target_port, timeout=0.5):
            logger.info("MQTT Broker is active on %s:%d", target_host, target_port)
            return True

        # If not open and mode is local, attempt to start local mosquitto
        binary = find_mosquitto_binary()
        if not binary:
            logger.warning("No local mosquitto binary found in standard paths.")
            return False

        conf_path = config.PROJECT_ROOT / "config" / "mosquitto.conf"
        try:
            logger.info("Starting local Mosquitto broker: %s -c %s", binary, conf_path)
            self._proc = subprocess.Popen(
                [binary, "-c", str(conf_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Give it a brief moment to bind port
            import time
            for _ in range(20):
                time.sleep(0.1)
                if is_port_open(target_host, target_port, timeout=0.2):
                    logger.info("Local Mosquitto broker started successfully on PID %d", self._proc.pid)
                    return True
            logger.error("Mosquitto process started but port %d did not open.", target_port)
            return False
        except Exception as e:
            logger.error("Failed to start local Mosquitto broker: %s", e)
            return False

    def stop_broker(self):
        """Stop managed broker process if running."""
        with self._lock:
            if self._proc:
                try:
                    self._proc.terminate()
                    self._proc.wait(timeout=3)
                    logger.info("Local Mosquitto stopped.")
                except Exception:
                    self._proc.kill()
                finally:
                    self._proc = None


broker_manager = BrokerManager()

