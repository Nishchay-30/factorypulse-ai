"""
FactoryPulse AI - Standalone Model Evaluation Script
Loads trained model artifact and evaluates generalization performance on fresh scenarios.
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
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, accuracy_score, f1_score

from src.common.config import config
from ml.generate_dataset import generate_simulation_runs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("EvaluateModel")


def evaluate():
    model_path = config.ML_MODEL_PATH
    if not model_path.exists():
        logger.error("Trained model not found at %s. Please run train.py first.", model_path)
        return

    logger.info("Loading serialized model package from %s...", model_path)
    pkg = joblib.load(model_path)
    model = pkg["model"]
    features = pkg["feature_columns"]
    version = pkg.get("version", "unknown")

    # Generate fresh evaluation simulation run
    logger.info("Generating fresh benchmark evaluation dataset (5 episodes)...")
    eval_df = generate_simulation_runs(num_runs=5, duration_sec=200)

    X_eval = eval_df[features]
    y_eval = eval_df["target_bottleneck_60s"]

    logger.info("Evaluating %d unseen benchmark samples...", len(eval_df))
    preds = model.predict(X_eval)
    probs = model.predict_proba(X_eval)[:, 1]

    acc = accuracy_score(y_eval, preds)
    f1 = f1_score(y_eval, preds, zero_division=0)
    cm = confusion_matrix(y_eval, preds)
    report = classification_report(y_eval, preds, target_names=["Normal", "Bottleneck"], digits=4)

    logger.info("=== Model Version: %s Benchmark Report ===", version)
    logger.info("Overall Accuracy: %.4f", acc)
    logger.info("F1 Score:         %.4f", f1)
    if len(np.unique(y_eval)) > 1:
        auc = roc_auc_score(y_eval, probs)
        logger.info("ROC-AUC:          %.4f", auc)
    print("\n" + report)
    print("Confusion Matrix:\n", cm)


if __name__ == "__main__":
    evaluate()

