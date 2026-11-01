"""
Integration tests for End-to-End Pipeline (Simulator -> MQTT/Bus -> CSV -> DB -> Alerts -> ML).
"""

import pytest
import pandas as pd
from src.simulator.factory_simulator import FactorySimulator
from src.ingestion.csv_logger import csv_logger
from src.database.db import db
from src.alerts.engine import alert_engine
from src.prediction.predictor import RealTimePredictor


def test_full_data_pipeline_end_to_end():
    sim = FactorySimulator()
    predictor = RealTimePredictor()

    # Step through 5 seconds of production
    for _ in range(5):
        step = sim.step()

        # 1. Log to CSV
        for st_id in ["station01", "station02", "station03"]:
            reading = step[st_id].model_dump()
            csv_logger.log_station_telemetry(reading)
            db.insert_sensor_reading(reading)
            alert_engine.evaluate_station_reading(reading)

        # 2. Line telemetry
        line = step["processed"].model_dump()
        csv_logger.log_line_telemetry(line)
        db.insert_production_metric(line)

        # 3. Predictor
        predictor.process_reading(step["station02"].model_dump())

    # Verify CSV files updated
    st2_csv = csv_logger.output_dir / "station02.csv"
    assert st2_csv.exists()
    df_csv = pd.read_csv(st2_csv)
    assert len(df_csv) >= 5

    # Verify SQLite persistence
    db_readings = db.get_recent_readings(station_id="station02", limit=10)
    assert len(db_readings) >= 5

    # Verify predictions persisted
    preds = db.get_recent_predictions(limit=10)
    assert len(preds) >= 5

