"""
FactoryPulse AI - Real-Time Bottleneck Inference Engine
Subscribes to live telemetry, engineers rolling features, and performs AI bottleneck inference.
"""

import time
import json
import uuid
import joblib
import logging
import threading
from typing import Dict, Any, List, Optional
from collections import deque
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from src.common.config import config
from src.common.schemas import PredictionMessage
from src.database.db import db
from src.mqtt.client import MQTTClientWrapper

logger = logging.getLogger("FactoryPulse.Predictor")


class RealTimePredictor:
    """Performs real-time machine learning inference for future bottleneck prediction."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = config.ML_MODEL_PATH if model_path is None else Path(model_path)
        self.model = None
        self.feature_columns = []
        self.model_version = "unavailable"
        self._load_model()

        # Telemetry history buffer for rolling window calculations
        self._history_lock = threading.Lock()
        self.history = deque(maxlen=20)
        self.last_line_metric: Dict[str, Any] = {
            "demand_rate": config.DEMAND_RATE_UNITS_PER_MIN,
            "line_throughput": 15.0,
            "total_wip": 15,
        }

        self.mqtt_client = MQTTClientWrapper(
            client_id_suffix="ai_predictor",
            on_message_callback=self._handle_telemetry,
        )
        self.running = False

    def _load_model(self):
        """Load serialized Random Forest model pipeline."""
        if self.model_path.exists():
            try:
                pkg = joblib.load(self.model_path)
                self.model = pkg["model"]
                self.feature_columns = pkg["feature_columns"]
                self.model_version = pkg.get("version", "rf_v1.0")
                logger.info("Loaded AI model '%s' successfully from %s", self.model_version, self.model_path)
            except Exception as e:
                logger.error("Failed to load model from %s: %s", self.model_path, e)
                self.model = None
                self.model_version = "corrupted_fallback"
        else:
            logger.warning("No model found at %s. Operating in rule-based fallback mode.", self.model_path)
            self.model = None
            self.model_version = "rules_fallback"

    def _handle_telemetry(self, topic: str, payload: Dict[str, Any]):
        """Callback for incoming telemetry messages."""
        if topic == config.TOPIC_PROCESSED:
            self.last_line_metric = payload
            return

        # Station 2 is the primary focal station
        if topic == config.TOPIC_STATION2:
            self.process_reading(payload)

    def process_reading(self, reading: Dict[str, Any]) -> Optional[PredictionMessage]:
        """Extract rolling features and perform prediction."""
        with self._history_lock:
            self.history.append(reading)
            buf = list(self.history)

        if not buf:
            return None

        # Build feature vector
        features = self._extract_features(buf, reading)

        # Inference
        if self.model is not None:
            try:
                feat_df = pd.DataFrame([features])
                # Ensure correct column ordering
                feat_df = feat_df[self.feature_columns]
                probs = self.model.predict_proba(feat_df)[0]
                risk_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
                is_bottleneck = bool(risk_prob >= 0.5)
                confidence = float(max(probs))
            except Exception as e:
                logger.error("Inference exception: %s. Using rule-based fallback.", e)
                risk_prob, is_bottleneck, confidence = self._rule_fallback(reading)
        else:
            risk_prob, is_bottleneck, confidence = self._rule_fallback(reading)

        pred_msg = PredictionMessage(
            prediction_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            prediction_horizon_sec=config.ML_PREDICTION_HORIZON_SEC,
            bottleneck_predicted=is_bottleneck,
            predicted_station="station02" if is_bottleneck else None,
            risk_probability=round(risk_prob, 3),
            confidence=round(confidence, 3),
            model_version=self.model_version,
            features_used={k: round(v, 2) for k, v in features.items() if k in ["rpm", "queue_length", "rpm_rolling_mean", "rpm_trend", "queue_growth_rate"]},
        )

        # Persist to database
        db.insert_prediction(pred_msg.model_dump())

        # Publish to MQTT topic
        self.mqtt_client.publish(config.TOPIC_PREDICTIONS, pred_msg.model_dump())

        return pred_msg

    def _extract_features(self, history: List[Dict[str, Any]], current: Dict[str, Any]) -> Dict[str, float]:
        """Calculate historical rolling window features without data leakage."""
        rpms = [float(r.get("rpm", 0.0)) for r in history]
        tps = [float(r.get("throughput", 0.0)) for r in history]
        queues = [float(r.get("queue_length", 0)) for r in history]

        rpm_mean = float(np.mean(rpms))
        rpm_std = float(np.std(rpms)) if len(rpms) > 1 else 0.0

        # Trends (rate of change over last 5 samples)
        rpm_trend = (rpms[-1] - rpms[0]) / max(1, len(rpms)) if len(rpms) > 1 else 0.0
        tp_trend = (tps[-1] - tps[0]) / max(1, len(tps)) if len(tps) > 1 else 0.0
        q_growth = (queues[-1] - queues[0]) / max(1, len(queues)) if len(queues) > 1 else 0.0

        demand = float(self.last_line_metric.get("demand_rate", config.DEMAND_RATE_UNITS_PER_MIN))
        curr_tp = float(current.get("throughput", 0.0))

        return {
            "rpm": float(current.get("rpm", 0.0)),
            "cycle_time": float(current.get("cycle_time", 4.0)),
            "throughput": curr_tp,
            "utilization": float(current.get("utilization", 0.8)),
            "queue_length": float(current.get("queue_length", 0)),
            "vibration": float(current.get("vibration", 1.2) or 1.2),
            "temperature": float(current.get("temperature", 36.5) or 36.5),
            "current": float(current.get("current", 0.85) or 0.85),
            "demand_rate": demand,
            "line_throughput": float(self.last_line_metric.get("line_throughput", 15.0)),
            "total_wip": float(self.last_line_metric.get("total_wip", 15)),
            "rpm_rolling_mean": rpm_mean,
            "rpm_rolling_std": rpm_std,
            "rpm_trend": rpm_trend,
            "tp_trend": tp_trend,
            "queue_growth_rate": q_growth,
            "tp_to_demand_ratio": curr_tp / max(1.0, demand),
        }

    def _rule_fallback(self, reading: Dict[str, Any]) -> tuple[float, bool, float]:
        """Heuristic rule-based fallback when model is unavailable."""
        rpm = float(reading.get("rpm", 1500.0))
        queue = int(reading.get("queue_length", 5))

        if rpm < 500 or queue >= 25:
            return 0.95, True, 0.90
        elif rpm < 1000 or queue >= 15:
            return 0.70, True, 0.75
        elif rpm < 1300 or queue >= 10:
            return 0.40, False, 0.65
        else:
            return 0.10, False, 0.90

    def start(self):
        self.mqtt_client.connect(timeout=5.0)
        self.mqtt_client.subscribe(config.TOPIC_STATION2)
        self.mqtt_client.subscribe(config.TOPIC_PROCESSED)
        self.running = True
        logger.info("Real-Time AI Predictor active and monitoring telemetry.")

        try:
            while self.running:
                time.sleep(1.0)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.running = False
        self.mqtt_client.disconnect()
        logger.info("Real-Time AI Predictor stopped.")


if __name__ == "__main__":
    predictor = RealTimePredictor()
    predictor.start()

