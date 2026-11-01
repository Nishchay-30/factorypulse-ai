"""
FactoryPulse AI - Machine Learning Training Pipeline
Trains a Random Forest Classifier and evaluates against a rule-based baseline.
Saves model artifact, metrics, and metadata without data leakage.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
import logging
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

from src.common.config import config
from src.database.db import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TrainPipeline")

FEATURE_COLUMNS = [
    "rpm",
    "cycle_time",
    "throughput",
    "utilization",
    "queue_length",
    "vibration",
    "temperature",
    "current",
    "demand_rate",
    "line_throughput",
    "total_wip",
    "rpm_rolling_mean",
    "rpm_rolling_std",
    "rpm_trend",
    "tp_trend",
    "queue_growth_rate",
    "tp_to_demand_ratio",
]

TARGET_COLUMN = "target_bottleneck_60s"


class RuleBasedBaseline:
    """Industrial rule-based heuristic for baseline comparison."""

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        # Predict bottleneck if queue >= 10 or rpm rolling mean < 1100
        preds = (X["queue_length"] >= 10) | (X["rpm_rolling_mean"] < 1100.0)
        return preds.astype(int).values

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        preds = self.predict(X)
        probs = np.zeros((len(preds), 2))
        probs[:, 1] = preds.astype(float)
        probs[:, 0] = 1.0 - probs[:, 1]
        return probs


def train():
    data_path = config.PROJECT_ROOT / "data" / "synthetic" / "training_dataset.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Training data not found at {data_path}. Run generate_dataset.py first.")

    logger.info("Loading dataset from %s...", data_path)
    df = pd.read_csv(data_path)

    # Episode-based train/test split to guarantee NO DATA LEAKAGE
    run_ids = df["run_id"].unique()
    np.random.seed(42)
    test_runs = set(np.random.choice(run_ids, size=max(2, int(len(run_ids) * 0.2)), replace=False))
    train_runs = [r for r in run_ids if r not in test_runs]

    train_df = df[df["run_id"].isin(train_runs)].copy()
    test_df = df[df["run_id"].isin(test_runs)].copy()

    logger.info("Train set: %d samples (%d episodes) | Test set: %d samples (%d episodes)",
                len(train_df), len(train_runs), len(test_df), len(test_runs))

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET_COLUMN]

    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET_COLUMN]

    # --------------------------------------------------------------------------
    # 1. Rule-based Baseline
    # --------------------------------------------------------------------------
    baseline = RuleBasedBaseline()
    baseline_preds = baseline.predict(X_test)
    baseline_f1 = f1_score(y_test, baseline_preds, zero_division=0)
    baseline_acc = accuracy_score(y_test, baseline_preds)
    logger.info("Baseline Rule-Based Model -> Accuracy: %.3f, F1-Score: %.3f", baseline_acc, baseline_f1)

    # --------------------------------------------------------------------------
    # 2. Random Forest Model
    # --------------------------------------------------------------------------
    logger.info("Training Random Forest Classifier...")
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)

    # Evaluation
    test_preds = rf.predict(X_test)
    test_probs = rf.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, test_preds))
    prec = float(precision_score(y_test, test_preds, zero_division=0))
    rec = float(recall_score(y_test, test_preds, zero_division=0))
    f1 = float(f1_score(y_test, test_preds, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, test_probs)) if len(np.unique(y_test)) > 1 else None
    cm = confusion_matrix(y_test, test_preds).tolist()

    logger.info("=== Random Forest Evaluation on Unseen Test Episodes ===")
    logger.info("Accuracy:  %.4f", acc)
    logger.info("Precision: %.4f", prec)
    logger.info("Recall:    %.4f", rec)
    logger.info("F1-Score:  %.4f", f1)
    if roc_auc:
        logger.info("ROC-AUC:   %.4f", roc_auc)
    logger.info("Confusion Matrix: %s", cm)

    # Feature Importance
    importances = dict(zip(FEATURE_COLUMNS, [float(v) for v in rf.feature_importances_]))
    sorted_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    logger.info("Top 5 Predictive Features:")
    for feat, imp in sorted_features[:5]:
        logger.info("  - %-20s: %.4f", feat, imp)

    # --------------------------------------------------------------------------
    # 3. Model Serialization & Metadata
    # --------------------------------------------------------------------------
    models_dir = config.PROJECT_ROOT / "ml" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    model_save_path = models_dir / "bottleneck_rf_model.joblib"
    meta_save_path = models_dir / "model_metadata.json"

    # Save model artifact
    joblib.dump(
        {
            "model": rf,
            "feature_columns": FEATURE_COLUMNS,
            "target_column": TARGET_COLUMN,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "version": "rf_v1.0",
        },
        model_save_path,
    )
    logger.info("Trained model serialized to %s", model_save_path)

    metadata = {
        "model_version": "rf_v1.0",
        "algorithm": "RandomForestClassifier",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4) if roc_auc else None,
        "confusion_matrix": cm,
        "feature_importances": importances,
        "baseline_comparison": {
            "baseline_accuracy": round(baseline_acc, 4),
            "baseline_f1": round(baseline_f1, 4),
            "rf_f1_improvement": round(f1 - baseline_f1, 4),
        },
        "parameters": {
            "n_estimators": 100,
            "max_depth": 8,
            "prediction_horizon_sec": config.ML_PREDICTION_HORIZON_SEC,
            "class_weight": "balanced",
        },
    }

    with open(meta_save_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info("Metadata saved to %s", meta_save_path)

    # Persist to SQLite model_metadata table
    db.save_model_metadata(metadata)
    logger.info("Model metadata successfully saved to SQLite database.")


if __name__ == "__main__":
    train()

