"""
FactoryPulse AI - Robust MQTT Client Wrapper
Supports:
1. HiveMQ Cloud (TLS 8883, SASL auth)
2. Local Mosquitto Broker (Port 1883)
3. In-Process Message Bus (Offline / Sandbox Fallback when TCP loopback is restricted)
"""

import ssl
import time
import json
import socket
import fnmatch
import logging
import threading
from typing import Callable, Optional, Dict, Any, List
import paho.mqtt.client as mqtt

from src.common.config import config

logger = logging.getLogger("FactoryPulse.MQTT")
if not logger.handlers:
    logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))


class InProcessMessageBus:
    """Thread-safe, topic-matching in-process bus with MQTT wildcard semantics."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(InProcessMessageBus, cls).__new__(cls)
                cls._instance._subscribers = []  # list of (pattern, callback)
                cls._retained = {}  # topic -> payload
                cls._bus_lock = threading.Lock()
            return cls._instance

    def subscribe(self, topic: str, callback: Callable[[str, Dict[str, Any]], None]):
        with self._bus_lock:
            self._subscribers.append((topic, callback))
            # Deliver any matching retained messages
            for retained_topic, retained_payload in self._retained.items():
                if self._matches(retained_topic, topic):
                    try:
                        callback(retained_topic, retained_payload)
                    except Exception as e:
                        logger.error("Error delivering retained message: %s", e)

    def unsubscribe(self, callback: Callable):
        with self._bus_lock:
            self._subscribers = [(top, cb) for top, cb in self._subscribers if cb != callback]

    def publish(self, topic: str, payload: Dict[str, Any], retain: bool = False):
        with self._bus_lock:
            if retain:
                self._retained[topic] = payload
            subs = list(self._subscribers)

        for pattern, callback in subs:
            if self._matches(topic, pattern):
                try:
                    # Execute callback
                    callback(topic, payload)
                except Exception as e:
                    logger.error("Error in bus callback for topic %s: %s", topic, e)

    @staticmethod
    def _matches(topic: str, pattern: str) -> bool:
        """Match MQTT topics with '+' and '#' wildcards."""
        if pattern == "#":
            return True
        if pattern == topic:
            return True
        # Convert MQTT wildcards to fnmatch regex pattern
        # '+' matches a single level (anything except '/')
        # '#' matches multiple levels
        fn_pattern = pattern.replace("+", "[^/]+").replace("#", ".*")
        import re
        return bool(re.fullmatch(fn_pattern, topic))


bus = InProcessMessageBus()


class MQTTClientWrapper:
    """Enterprise-grade MQTT Client supporting TLS, HiveMQ Cloud, Mosquitto, and In-Process Bus."""

    def __init__(
        self,
        client_id_suffix: str = "service",
        on_message_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        use_cloud: Optional[bool] = None,
    ):
        self.client_id = f"{config.MQTT_CLIENT_ID_PREFIX}{client_id_suffix}_{int(time.time() * 1000) % 10000}"
        self.on_message_callback = on_message_callback

        if use_cloud is not None:
            self.use_cloud = use_cloud
        else:
            self.use_cloud = (config.MQTT_MODE == "hivemq" and bool(config.MQTT_HIVEMQ_HOST))

        self._connected = False
        self._in_process_mode = False
        self._lock = threading.Lock()
        self._subscriptions: List[tuple[str, int]] = []
        self._connection_info: Dict[str, Any] = {
            "mode": "hivemq" if self.use_cloud else "local",
            "host": "",
            "port": 0,
            "connected": False,
            "in_process_fallback": False,
            "reconnect_attempts": 0,
            "messages_published": 0,
            "messages_received": 0,
            "last_error": None,
        }

        self._init_paho()

    def _init_paho(self):
        try:
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=self.client_id,
                clean_session=True,
            )
        except (AttributeError, TypeError):
            self.client = mqtt.Client(
                client_id=self.client_id,
                clean_session=True,
            )

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish

        if self.use_cloud and config.MQTT_HIVEMQ_HOST:
            self.host = config.MQTT_HIVEMQ_HOST
            self.port = config.MQTT_HIVEMQ_PORT
            self.client.username_pw_set(
                username=config.MQTT_HIVEMQ_USERNAME,
                password=config.MQTT_HIVEMQ_PASSWORD,
            )
            if config.MQTT_HIVEMQ_USE_TLS:
                self.client.tls_set(
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=ssl.PROTOCOL_TLS_CLIENT,
                )
            self._connection_info["mode"] = "hivemq_cloud"
        else:
            self.host = config.MQTT_LOCAL_HOST
            self.port = config.MQTT_LOCAL_PORT
            self._connection_info["mode"] = "local_mosquitto"

        self._connection_info["host"] = self.host
        self._connection_info["port"] = self.port

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        rc = getattr(reason_code, "value", reason_code)
        if rc == 0:
            with self._lock:
                self._connected = True
                self._in_process_mode = False
                self._connection_info["connected"] = True
                self._connection_info["in_process_fallback"] = False
                self._connection_info["last_error"] = None
            logger.info("Connected to MQTT broker at %s:%d (%s)", self.host, self.port, self._connection_info["mode"])

            for topic, qos in self._subscriptions:
                self.client.subscribe(topic, qos=qos)
        else:
            with self._lock:
                self._connected = False
                self._connection_info["connected"] = False
                self._connection_info["last_error"] = f"Connection error: rc={rc}"
            logger.error("MQTT connection rejected with rc=%s", rc)

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code=None, properties=None):
        with self._lock:
            self._connected = False
            self._connection_info["connected"] = False
        rc = getattr(reason_code, "value", reason_code) if reason_code is not None else disconnect_flags
        logger.warning("Disconnected from MQTT broker (rc=%s)", rc)

    def _on_publish(self, client, userdata, mid, reason_code=None, properties=None):
        with self._lock:
            self._connection_info["messages_published"] += 1

    def _on_message(self, client, userdata, msg):
        with self._lock:
            self._connection_info["messages_received"] += 1
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            payload = {"raw_payload": msg.payload.decode("utf-8", errors="replace")}

        if self.on_message_callback:
            try:
                self.on_message_callback(msg.topic, payload)
            except Exception as e:
                logger.error("Error in on_message callback for %s: %s", msg.topic, e, exc_info=True)

    def _bus_message_handler(self, topic: str, payload: Dict[str, Any]):
        """Handler when running over the in-process bus."""
        with self._lock:
            self._connection_info["messages_received"] += 1
        if self.on_message_callback:
            try:
                self.on_message_callback(topic, payload)
            except Exception as e:
                logger.error("Error in bus message callback for %s: %s", topic, e)

    def connect(self, timeout: float = 3.0) -> bool:
        """Connect to broker, or smoothly switch to in-process bus if socket connection is disallowed."""
        logger.info("Connecting MQTT client (%s) to %s:%d...", self.client_id, self.host, self.port)
        try:
            self.client.connect_async(self.host, self.port, keepalive=config.MQTT_LOCAL_KEEPALIVE)
            self.client.loop_start()

            start = time.time()
            while time.time() - start < timeout:
                if self._connected:
                    return True
                time.sleep(0.05)
        except (OSError, socket.error, Exception) as e:
            logger.warning("Network socket connection unavailable (%s). Activating In-Process Bus fallback.", e)
            self._activate_in_process_fallback(str(e))
            return True

        if not self._connected:
            logger.info("Broker not immediately responding; activating In-Process Bus fallback.")
            self._activate_in_process_fallback("Broker did not respond within timeout")
        return True

    def _activate_in_process_fallback(self, reason: str):
        with self._lock:
            self._connected = True
            self._in_process_mode = True
            self._connection_info["connected"] = True
            self._connection_info["in_process_fallback"] = True
            self._connection_info["mode"] = "in_process_bus"
            self._connection_info["last_error"] = f"Fallback active: {reason}"

        # Register subscriptions with the bus
        for topic, _ in self._subscriptions:
            bus.subscribe(topic, self._bus_message_handler)

    def subscribe(self, topic: str, qos: int = 1):
        with self._lock:
            if (topic, qos) not in self._subscriptions:
                self._subscriptions.append((topic, qos))
            in_process = self._in_process_mode
            connected = self._connected

        if in_process:
            bus.subscribe(topic, self._bus_message_handler)
        elif connected:
            self.client.subscribe(topic, qos=qos)

    def publish(self, topic: str, payload: Any, qos: int = 1, retain: bool = False) -> bool:
        try:
            if isinstance(payload, dict):
                data_dict = payload
                data_str = json.dumps(payload)
            elif hasattr(payload, "model_dump"):
                data_dict = payload.model_dump()
                data_str = json.dumps(data_dict)
            elif hasattr(payload, "dict"):
                data_dict = payload.dict()
                data_str = json.dumps(data_dict)
            else:
                data_str = str(payload)
                data_dict = {"raw": data_str}

            with self._lock:
                in_proc = self._in_process_mode
                self._connection_info["messages_published"] += 1

            if in_proc:
                bus.publish(topic, data_dict, retain=retain)
                return True
            else:
                info = self.client.publish(topic, data_str, qos=qos, retain=retain)
                return info.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error("Error publishing to %s: %s", topic, e)
            return False

    def disconnect(self):
        try:
            if self._in_process_mode:
                bus.unsubscribe(self._bus_message_handler)
            else:
                self.client.loop_stop()
                self.client.disconnect()
            with self._lock:
                self._connected = False
                self._connection_info["connected"] = False
        except Exception as e:
            logger.error("Error during disconnect: %s", e)

    @property
    def is_connected(self) -> bool:
        with self._lock:
            return self._connected

    @property
    def is_in_process_fallback(self) -> bool:
        with self._lock:
            return self._in_process_mode

    @property
    def connection_info(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._connection_info)
