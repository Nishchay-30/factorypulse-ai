"""
FactoryPulse AI - Industrial Alert Engine
Implements hysteresis, consecutive-reading verification, alert cooldowns,
severity levels (NORMAL, WARNING, CRITICAL), and persistence.
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from src.common.config import config
from src.common.schemas import AlertMessage, MotorCommand
from src.database.db import db
from src.mqtt.client import MQTTClientWrapper

logger = logging.getLogger("FactoryPulse.AlertEngine")


class AlertEngine:
    """Production rule engine with debounce, hysteresis, and cooldown protections."""

    def __init__(self, mqtt_client: Optional[MQTTClientWrapper] = None):
        self.mqtt_client = mqtt_client or MQTTClientWrapper(client_id_suffix="alert_engine")

        # Tracking state per (station_id, rule_code)
        # Structure: {(station_id, code): {"consecutive": int, "last_fired": float, "active": bool}}
        self.rule_states: Dict[tuple[str, str], Dict[str, Any]] = {}

        # Station nominal RPM lookups
        self.base_rpms = {
            "station01": config.STATION1_BASE_RPM,
            "station02": config.STATION2_BASE_RPM,
            "station03": config.STATION3_BASE_RPM,
        }

    def _get_state(self, station_id: str, rule_code: str) -> Dict[str, Any]:
        key = (station_id, rule_code)
        if key not in self.rule_states:
            self.rule_states[key] = {
                "consecutive_abnormal": 0,
                "consecutive_normal": 0,
                "last_fired_time": 0.0,
                "is_active": False,
                "last_severity": "NORMAL",
            }
        return self.rule_states[key]

    def evaluate_station_reading(self, reading: Dict[str, Any]):
        """Evaluate workstation reading against industrial rules."""
        station_id = reading.get("station_id")
        if not station_id:
            return

        rpm = float(reading.get("rpm", 0.0))
        queue_len = int(reading.get("queue_length", 0))
        throughput = float(reading.get("throughput", 0.0))
        base_rpm = self.base_rpms.get(station_id, 1500.0)

        # ----------------------------------------------------------------------
        # Rule 1: Machine Stoppage
        # ----------------------------------------------------------------------
        if rpm < 50.0:
            self._trigger_rule(
                station_id=station_id,
                rule_code="MACHINE_STOPPED",
                severity="CRITICAL",
                message=f"{station_id} has stopped unexpectedly (RPM: {rpm:.1f})",
                measured_val=rpm,
                threshold_val=50.0,
            )
        else:
            self._clear_rule(station_id, "MACHINE_STOPPED", rpm, 50.0)

        # ----------------------------------------------------------------------
        # Rule 2: Low RPM / Machine Slowdown
        # ----------------------------------------------------------------------
        rpm_ratio = rpm / max(1.0, base_rpm)
        if 50.0 <= rpm < (base_rpm * config.ALERT_RPM_CRITICAL_RATIO):
            self._trigger_rule(
                station_id=station_id,
                rule_code="RPM_CRITICAL_LOW",
                severity="CRITICAL",
                message=f"{station_id} RPM severely degraded ({rpm:.1f} RPM, {rpm_ratio*100:.0f}% of base)",
                measured_val=rpm,
                threshold_val=base_rpm * config.ALERT_RPM_CRITICAL_RATIO,
            )
        elif (base_rpm * config.ALERT_RPM_CRITICAL_RATIO) <= rpm < (base_rpm * config.ALERT_RPM_WARNING_RATIO):
            self._trigger_rule(
                station_id=station_id,
                rule_code="RPM_WARNING_LOW",
                severity="WARNING",
                message=f"{station_id} RPM below nominal threshold ({rpm:.1f} RPM)",
                measured_val=rpm,
                threshold_val=base_rpm * config.ALERT_RPM_WARNING_RATIO,
            )
        else:
            self._clear_rule(station_id, "RPM_CRITICAL_LOW", rpm, base_rpm * config.ALERT_RPM_CRITICAL_RATIO)
            self._clear_rule(station_id, "RPM_WARNING_LOW", rpm, base_rpm * config.ALERT_RPM_WARNING_RATIO)

        # ----------------------------------------------------------------------
        # Rule 3: Buffer Queue Accumulation
        # ----------------------------------------------------------------------
        if queue_len >= config.ALERT_QUEUE_CRITICAL_THRESHOLD:
            self._trigger_rule(
                station_id=station_id,
                rule_code="QUEUE_CRITICAL_OVERFLOW",
                severity="CRITICAL",
                message=f"{station_id} upstream queue critical ({queue_len} units >= {config.ALERT_QUEUE_CRITICAL_THRESHOLD})",
                measured_val=float(queue_len),
                threshold_val=float(config.ALERT_QUEUE_CRITICAL_THRESHOLD),
            )
        elif queue_len >= config.ALERT_QUEUE_WARNING_THRESHOLD:
            self._trigger_rule(
                station_id=station_id,
                rule_code="QUEUE_WARNING_HIGH",
                severity="WARNING",
                message=f"{station_id} upstream queue accumulating ({queue_len} units >= {config.ALERT_QUEUE_WARNING_THRESHOLD})",
                measured_val=float(queue_len),
                threshold_val=float(config.ALERT_QUEUE_WARNING_THRESHOLD),
            )
        else:
            self._clear_rule(station_id, "QUEUE_CRITICAL_OVERFLOW", float(queue_len), float(config.ALERT_QUEUE_CRITICAL_THRESHOLD))
            self._clear_rule(station_id, "QUEUE_WARNING_HIGH", float(queue_len), float(config.ALERT_QUEUE_WARNING_THRESHOLD))

    def _trigger_rule(self, station_id: str, rule_code: str, severity: str, message: str, measured_val: float, threshold_val: float):
        state = self._get_state(station_id, rule_code)
        now = time.time()
        state["consecutive_abnormal"] += 1
        state["consecutive_normal"] = 0

        # Require consecutive abnormal counts (hysteresis)
        if state["consecutive_abnormal"] >= config.ALERT_HYSTERESIS_COUNT:
            # Check cooldown
            if (now - state["last_fired_time"]) >= config.ALERT_COOLDOWN_SECONDS:
                state["last_fired_time"] = now
                state["is_active"] = True
                state["last_severity"] = severity

                alert = AlertMessage(
                    alert_id=str(uuid.uuid4()),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    station_id=station_id,
                    severity=severity,
                    alert_code=rule_code,
                    message=message,
                    measured_value=measured_val,
                    threshold_value=threshold_val,
                    acknowledged=False,
                    resolved=False,
                )

                # Persist to database
                db.insert_alert(alert.model_dump())

                # Publish to MQTT
                self.mqtt_client.publish(config.TOPIC_ALERTS, alert.model_dump())
                logger.warning("[ALERT %s] %s: %s", severity, station_id, message)

    def _clear_rule(self, station_id: str, rule_code: str, measured_val: float, threshold_val: float):
        state = self._get_state(station_id, rule_code)
        if not state["is_active"]:
            state["consecutive_abnormal"] = 0
            return

        state["consecutive_normal"] += 1
        state["consecutive_abnormal"] = 0

        if state["consecutive_normal"] >= config.ALERT_HYSTERESIS_COUNT:
            state["is_active"] = False
            state["consecutive_normal"] = 0

            # Resolution event
            alert = AlertMessage(
                alert_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc).isoformat(),
                station_id=station_id,
                severity="NORMAL",
                alert_code=f"{rule_code}_RESOLVED",
                message=f"{station_id} condition normalized for {rule_code}",
                measured_value=measured_val,
                threshold_value=threshold_val,
                acknowledged=True,
                resolved=True,
            )
            db.insert_alert(alert.model_dump())
            self.mqtt_client.publish(config.TOPIC_ALERTS, alert.model_dump())
            logger.info("[ALERT RESOLVED] %s: %s normalized.", station_id, rule_code)


alert_engine = AlertEngine()

