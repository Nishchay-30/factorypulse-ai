"""
Unit tests for Machine Learning model loading, feature engineering, and inference.
"""

import pytest
from src.prediction.predictor import RealTimePredictor


def test_predictor_model_loading_and_inference():
    predictor = RealTimePredictor()
    assert predictor.model_version in ["rf_v1.0", "rules_fallback"]

    reading = {
        "station_id": "station02",
        "rpm": 1490.0,
        "cycle_time": 4.0,
        "throughput": 14.8,
        "utilization": 0.85,
        "queue_length": 5,
        "status": "NORMAL",
        "vibration": 1.2,
        "temperature": 36.5,
        "current": 0.85,
    }

    pred = predictor.process_reading(reading)
    assert pred is not None
    assert 0.0 <= pred.risk_probability <= 1.0
    assert isinstance(pred.bottleneck_predicted, bool)
    assert "rpm" in pred.features_used

