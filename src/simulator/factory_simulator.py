"""
FactoryPulse AI - Three-Workstation Factory Material Flow Simulator
Models physical manufacturing dynamics: WIP flow, queues, cycle times, motor RPM, and degradation.
"""

import time
import math
import random
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from src.common.config import config
from src.common.schemas import StationTelemetry, ProcessedLineTelemetry

logger = logging.getLogger("FactoryPulse.Simulator")


class Workstation:
    """Represents an industrial workstation on the production line."""

    def __init__(
        self,
        station_id: str,
        station_name: str,
        base_rpm: float,
        nominal_cycle_time: float,
        nominal_capacity: float,
        source: str = "simulated",
    ):
        self.station_id = station_id
        self.station_name = station_name
        self.base_rpm = base_rpm
        self.nominal_cycle_time = nominal_cycle_time
        self.nominal_capacity = nominal_capacity  # units / min
        self.source = source

        # Dynamic state
        self.current_rpm = base_rpm
        self.target_rpm = base_rpm
        self.queue_length = 5
        self.accumulated_processed = 0.0
        self.current_throughput = nominal_capacity
        self.current_cycle_time = nominal_cycle_time
        self.utilization = 0.85
        self.status = "NORMAL"

        # Sensor readings
        self.temperature = 36.5  # °C
        self.vibration = 1.2     # mm/s RMS
        self.current = 0.85      # Amperes (for motor station)

        # Hardware override
        self.hardware_active = False

    def update_hardware_reading(self, rpm: float, current: Optional[float] = None, temp: Optional[float] = None, vib: Optional[float] = None):
        """Update state using actual ESP32 hardware telemetry."""
        self.hardware_active = True
        self.source = "hardware"
        self.current_rpm = max(0.0, rpm)
        if current is not None:
            self.current = current
        if temp is not None:
            self.temperature = temp
        if vib is not None:
            self.vibration = vib

    def step(self, input_units: float, dt_sec: float) -> float:
        """
        Advance station by dt_sec seconds.
        input_units: incoming units added to queue during this time step.
        Returns: completed units outputted from this station.
        """
        # Add incoming units to queue
        self.queue_length = max(0, min(config.MAX_QUEUE_CAPACITY, self.queue_length + int(round(input_units))))

        # If simulated, smoothly move current_rpm toward target_rpm
        if not self.hardware_active:
            if abs(self.current_rpm - self.target_rpm) > 1.0:
                self.current_rpm += (self.target_rpm - self.current_rpm) * min(1.0, dt_sec * 0.5)
            # Add small industrial noise
            if self.current_rpm > 10.0:
                noise = random.gauss(0, 1.5)
                self.current_rpm = max(0.0, self.current_rpm + noise)

        # Calculate effective processing capacity
        rpm_ratio = self.current_rpm / max(1.0, self.base_rpm)
        effective_capacity = self.nominal_capacity * max(0.0, rpm_ratio)  # units / min

        # Calculate max units that can be processed in dt_sec
        max_possible_units = (effective_capacity / 60.0) * dt_sec

        # Actual units processed (cannot exceed available queue)
        if self.queue_length > 0 and effective_capacity > 0.05:
            units_processed = min(float(self.queue_length), max_possible_units)
            self.queue_length = max(0, int(round(self.queue_length - units_processed)))
            self.current_cycle_time = 60.0 / max(0.1, effective_capacity)
            self.utilization = min(1.0, max(0.1, effective_capacity / max(0.1, self.nominal_capacity)))
        else:
            units_processed = 0.0
            self.current_cycle_time = 99.9 if self.current_rpm < 10 else self.nominal_cycle_time
            self.utilization = 0.0 if self.current_rpm < 10 else 0.1

        # Real-time throughput (units per min)
        if dt_sec > 0:
            instant_tp = (units_processed / dt_sec) * 60.0
            # Exponential moving average for smooth display
            alpha = 0.15
            self.current_throughput = (1 - alpha) * self.current_throughput + alpha * instant_tp

        # Update physical sensor conditions based on stress
        if self.current_rpm < 50.0:
            self.status = "STOPPED"
            self.current = 0.0
            self.vibration = 0.05
        elif self.queue_length >= config.ALERT_QUEUE_CRITICAL_THRESHOLD or rpm_ratio <= config.ALERT_RPM_CRITICAL_RATIO:
            self.status = "CRITICAL"
            self.vibration = min(8.0, 3.5 + random.uniform(0.5, 2.0))
            self.temperature = min(75.0, self.temperature + 0.15 * dt_sec)
            self.current = min(3.0, 1.8 + random.uniform(0.2, 0.6))
        elif self.queue_length >= config.ALERT_QUEUE_WARNING_THRESHOLD or rpm_ratio <= config.ALERT_RPM_WARNING_RATIO:
            self.status = "WARNING"
            self.vibration = min(4.5, 2.0 + random.uniform(0.2, 0.8))
            self.temperature = min(55.0, self.temperature + 0.05 * dt_sec)
            self.current = min(2.0, 1.2 + random.uniform(0.1, 0.3))
        else:
            self.status = "NORMAL"
            self.vibration = max(0.8, 1.2 + random.uniform(-0.2, 0.2))
            self.temperature = max(35.0, self.temperature - 0.05 * dt_sec) if self.temperature > 37.0 else 36.5 + random.uniform(-0.5, 0.5)
            self.current = max(0.6, 0.85 + random.uniform(-0.05, 0.05))

        return units_processed

    def to_telemetry(self) -> StationTelemetry:
        """Generate validated Pydantic StationTelemetry instance."""
        return StationTelemetry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            station_id=self.station_id,
            station_name=self.station_name,
            source=self.source,
            rpm=round(self.current_rpm, 1),
            cycle_time=round(self.current_cycle_time, 2),
            throughput=round(max(0.0, self.current_throughput), 2),
            utilization=round(min(1.0, max(0.0, self.utilization)), 3),
            queue_length=int(self.queue_length),
            status=self.status,
            vibration=round(self.vibration, 2),
            temperature=round(self.temperature, 1),
            current=round(self.current, 2),
        )


class FactorySimulator:
    """Orchestrates 3-station production line simulation across various operating scenarios."""

    SCENARIOS = {
        "scenario_a": "Scenario A: Normal Factory Operation",
        "scenario_b": "Scenario B: Gradual Bottleneck Development",
        "scenario_c": "Scenario C: Sudden Machine Stoppage",
        "scenario_d": "Scenario D: High Production Demand",
        "scenario_e": "Scenario E: Recovery to Nominal Speed",
        "scenario_f": "Scenario F: Real ESP32 Hardware Integration",
    }

    def __init__(self):
        self.active_scenario = "scenario_a"
        self.scenario_start_time = time.time()
        self.time_scale = config.SIMULATION_TIME_SCALE
        self.is_running = True

        # Workstations
        self.station1 = Workstation(
            station_id="station01",
            station_name="Cutting",
            base_rpm=config.STATION1_BASE_RPM,
            nominal_cycle_time=config.STATION1_CYCLE_TIME_SEC,
            nominal_capacity=config.STATION1_CAPACITY_PER_MIN,
            source="simulated",
        )
        self.station2 = Workstation(
            station_id="station02",
            station_name="Drilling/Machining",
            base_rpm=config.STATION2_BASE_RPM,
            nominal_cycle_time=config.STATION2_CYCLE_TIME_SEC,
            nominal_capacity=config.STATION2_CAPACITY_PER_MIN,
            source="hardware" if config.STATION2_MODE == "hardware" else "simulated",
        )
        self.station3 = Workstation(
            station_id="station03",
            station_name="Packaging",
            base_rpm=config.STATION3_BASE_RPM,
            nominal_cycle_time=config.STATION3_CYCLE_TIME_SEC,
            nominal_capacity=config.STATION3_CAPACITY_PER_MIN,
            source="simulated",
        )

        self.demand_rate = config.DEMAND_RATE_UNITS_PER_MIN
        self.last_step_time = time.time()
        self.total_finished_goods = 0

    def set_scenario(self, scenario_key: str):
        """Switch active simulation scenario."""
        if scenario_key not in self.SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario_key}")
        self.active_scenario = scenario_key
        self.scenario_start_time = time.time()
        logger.info("Active scenario switched to: %s", self.SCENARIOS[scenario_key])

        # Immediate scenario adjustments
        if scenario_key == "scenario_a":
            self.station2.hardware_active = False
            self.station2.source = "simulated"
            self.station2.target_rpm = config.STATION2_BASE_RPM
            self.demand_rate = config.DEMAND_RATE_UNITS_PER_MIN

        elif scenario_key == "scenario_c":
            self.station2.hardware_active = False
            self.station2.source = "simulated"
            self.station2.target_rpm = 0.0
            self.station2.current_rpm = 0.0

        elif scenario_key == "scenario_d":
            self.station2.hardware_active = False
            self.station2.source = "simulated"
            self.station2.target_rpm = config.STATION2_BASE_RPM
            self.demand_rate = 24.0  # High demand exceeding station capacity

        elif scenario_key == "scenario_e":
            self.station2.hardware_active = False
            self.station2.source = "simulated"
            self.station2.target_rpm = config.STATION2_BASE_RPM
            self.demand_rate = config.DEMAND_RATE_UNITS_PER_MIN

        elif scenario_key == "scenario_f":
            self.station2.hardware_active = True
            self.station2.source = "hardware"

    def reset(self):
        """Reset all queues and parameters to factory default."""
        self.station1.queue_length = 5
        self.station1.current_rpm = config.STATION1_BASE_RPM
        self.station1.target_rpm = config.STATION1_BASE_RPM

        self.station2.queue_length = 6
        self.station2.current_rpm = config.STATION2_BASE_RPM
        self.station2.target_rpm = config.STATION2_BASE_RPM
        self.station2.hardware_active = False
        self.station2.source = "simulated"

        self.station3.queue_length = 4
        self.station3.current_rpm = config.STATION3_BASE_RPM
        self.station3.target_rpm = config.STATION3_BASE_RPM

        self.demand_rate = config.DEMAND_RATE_UNITS_PER_MIN
        self.active_scenario = "scenario_a"
        self.scenario_start_time = time.time()
        self.total_finished_goods = 0
        logger.info("Factory simulation reset to initial state.")

    def step(self, dt_override: Optional[float] = None) -> Dict[str, Any]:
        """Advance the factory simulation by one step."""
        now = time.time()
        dt = dt_override if dt_override is not None else (now - self.last_step_time)
        self.last_step_time = now

        # Apply time scale
        effective_dt = max(0.1, min(5.0, dt * self.time_scale))
        elapsed_scenario = (now - self.scenario_start_time) * self.time_scale

        # Dynamic behavior according to scenario
        if self.active_scenario == "scenario_b":
            # Gradual slowdown: RPM drops from 1500 to 450 over 90 scenario seconds
            progress = min(1.0, elapsed_scenario / 90.0)
            self.station2.target_rpm = config.STATION2_BASE_RPM * (1.0 - 0.75 * progress)

        elif self.active_scenario == "scenario_c":
            self.station2.target_rpm = 0.0

        elif self.active_scenario == "scenario_e":
            # Smooth recovery back up to base RPM
            self.station2.target_rpm = config.STATION2_BASE_RPM

        # 1. Incoming demand units into Station 1
        incoming_units = (self.demand_rate / 60.0) * effective_dt

        # 2. Step Station 1
        st1_out = self.station1.step(incoming_units, effective_dt)

        # 3. Step Station 2 (fed by Station 1 output)
        st2_out = self.station2.step(st1_out, effective_dt)

        # 4. Step Station 3 (fed by Station 2 output)
        st3_out = self.station3.step(st2_out, effective_dt)
        self.total_finished_goods += int(round(st3_out))

        # 5. Bottleneck identification
        # The bottleneck is the station with lowest processing rate or highest queue constraint
        stations = [self.station1, self.station2, self.station3]
        bottleneck_candidate = max(stations, key=lambda s: s.queue_length)
        if bottleneck_candidate.queue_length < 8:
            # If all queues are low, check if any machine is stopped
            stopped = [s for s in stations if s.status == "STOPPED"]
            bottleneck_station_id = stopped[0].station_id if stopped else None
        else:
            bottleneck_station_id = bottleneck_candidate.station_id

        # Aggregated line telemetry
        total_wip = self.station1.queue_length + self.station2.queue_length + self.station3.queue_length
        line_tp = self.station3.current_throughput
        line_efficiency = min(1.0, line_tp / max(1.0, self.demand_rate))

        processed_line = ProcessedLineTelemetry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            demand_rate=round(self.demand_rate, 1),
            line_throughput=round(line_tp, 2),
            total_wip=total_wip,
            bottleneck_station=bottleneck_station_id,
            line_efficiency=round(line_efficiency, 3),
            stations={
                "station01": self.station1.to_telemetry().model_dump(),
                "station02": self.station2.to_telemetry().model_dump(),
                "station03": self.station3.to_telemetry().model_dump(),
            },
        )

        return {
            "station01": self.station1.to_telemetry(),
            "station02": self.station2.to_telemetry(),
            "station03": self.station3.to_telemetry(),
            "processed": processed_line,
        }

