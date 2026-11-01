"""
FactoryPulse AI - Synthetic Training Dataset Generator
Simulates diverse industrial factory operating regimes and constructs
future-looking bottleneck targets (60-second horizon) without data leakage.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import time
import random
import logging
import pandas as pd
import numpy as np

from src.common.config import config
from src.simulator.factory_simulator import FactorySimulator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GenerateDataset")


def generate_simulation_runs(num_runs: int = 12, duration_sec: int = 300) -> pd.DataFrame:
    """
    Generate multiple independent factory runs with varying scenarios:
    - Normal operation
    - Gradual wear & slowdown
    - Sudden motor stalls
    - Overload demand surges
    - Recovery cycles
    """
    logger.info("Generating %d simulation runs of %d seconds each...", num_runs, duration_sec)
    all_rows = []

    scenarios = ["scenario_a", "scenario_b", "scenario_c", "scenario_d", "scenario_e"]

    for run_id in range(1, num_runs + 1):
        # Choose primary scenario for this run
        scenario = random.choice(scenarios)
        sim = FactorySimulator()
        sim.time_scale = 1.0
        sim.set_scenario(scenario)

        # Randomize demand slightly per run
        sim.demand_rate = random.uniform(13.0, 18.0) if scenario != "scenario_d" else random.uniform(21.0, 26.0)

        dt = 1.0  # 1 second step
        sim_time = 0.0

        run_records = []
        while sim_time < duration_sec:
            # Random scenario shifts in the middle of long runs
            if sim_time == 120 and scenario == "scenario_a" and random.random() < 0.5:
                sim.set_scenario("scenario_b")
            elif sim_time == 180 and scenario == "scenario_b" and random.random() < 0.4:
                sim.set_scenario("scenario_e")

            step = sim.step(dt_override=dt)
            st1 = step["station01"]
            st2 = step["station02"]
            st3 = step["station03"]
            line = step["processed"]

            record = {
                "run_id": run_id,
                "sim_time": sim_time,
                # Station 2 (Focal Workstation) Raw
                "rpm": st2.rpm,
                "cycle_time": st2.cycle_time,
                "throughput": st2.throughput,
                "utilization": st2.utilization,
                "queue_length": st2.queue_length,
                "status": st2.status,
                "vibration": st2.vibration,
                "temperature": st2.temperature,
                "current": st2.current,
                # Line context
                "demand_rate": line.demand_rate,
                "line_throughput": line.line_throughput,
                "total_wip": line.total_wip,
                # Upstream & Downstream context
                "st1_queue": st1.queue_length,
                "st1_throughput": st1.throughput,
                "st3_queue": st3.queue_length,
            }
            run_records.append(record)
            sim_time += dt

        # Convert run to DataFrame
        run_df = pd.DataFrame(run_records)

        # ----------------------------------------------------------------------
        # Feature Engineering (Strictly within historical window <= t)
        # ----------------------------------------------------------------------
        w = config.ML_ROLLING_WINDOW_SIZE  # e.g., 10 seconds

        run_df["rpm_rolling_mean"] = run_df["rpm"].rolling(window=w, min_periods=1).mean()
        run_df["rpm_rolling_std"] = run_df["rpm"].rolling(window=w, min_periods=1).std().fillna(0.0)
        run_df["rpm_trend"] = run_df["rpm"].diff(periods=5).fillna(0.0) / 5.0
        run_df["tp_trend"] = run_df["throughput"].diff(periods=5).fillna(0.0) / 5.0
        run_df["queue_growth_rate"] = run_df["queue_length"].diff(periods=5).fillna(0.0) / 5.0
        run_df["tp_to_demand_ratio"] = run_df["throughput"] / np.maximum(1.0, run_df["demand_rate"])

        # ----------------------------------------------------------------------
        # Target Construction: Future Bottleneck in [t+10s, t+60s]
        # A bottleneck occurs if future queue >= 15 or future RPM < 900 or status in ('CRITICAL', 'STOPPED')
        # ----------------------------------------------------------------------
        horizon_sec = config.ML_PREDICTION_HORIZON_SEC  # 60 seconds
        future_bottleneck_flags = []

        n = len(run_df)
        for i in range(n):
            # Look ahead from i+10 to i+horizon_sec
            future_start = min(n, i + 10)
            future_end = min(n, i + horizon_sec + 1)

            if future_start >= n or (future_end - future_start) < 10:
                # Near end of simulation run; omit or label based on remainder
                future_bottleneck_flags.append(np.nan)
            else:
                window_queues = run_df["queue_length"].iloc[future_start:future_end]
                window_rpms = run_df["rpm"].iloc[future_start:future_end]
                is_bottleneck = int(
                    (window_queues.max() >= config.ALERT_QUEUE_WARNING_THRESHOLD) or
                    (window_rpms.min() < 900.0)
                )
                future_bottleneck_flags.append(is_bottleneck)

        run_df["target_bottleneck_60s"] = future_bottleneck_flags
        # Drop rows where target cannot be evaluated (end of run)
        run_df = run_df.dropna(subset=["target_bottleneck_60s"]).copy()
        run_df["target_bottleneck_60s"] = run_df["target_bottleneck_60s"].astype(int)

        all_rows.append(run_df)

    final_df = pd.concat(all_rows, ignore_index=True)
    return final_df


def main():
    output_dir = config.PROJECT_ROOT / "data" / "synthetic"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "training_dataset.csv"

    # Generate 15 distinct runs x 300 seconds = ~4,500 samples
    df = generate_simulation_runs(num_runs=15, duration_sec=300)
    df.to_csv(csv_path, index=False)

    pos_samples = (df["target_bottleneck_60s"] == 1).sum()
    neg_samples = (df["target_bottleneck_60s"] == 0).sum()
    logger.info("Saved %d total training samples to %s", len(df), csv_path)
    logger.info("Class distribution -> Bottleneck (1): %d (%.1f%%), Normal (0): %d (%.1f%%)",
                pos_samples, (pos_samples / len(df)) * 100, neg_samples, (neg_samples / len(df)) * 100)


if __name__ == "__main__":
    main()
