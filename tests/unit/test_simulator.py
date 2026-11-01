"""
Unit tests for FactorySimulator and Workstation physics.
"""

import pytest
from src.simulator.factory_simulator import FactorySimulator, Workstation
from src.common.config import config


def test_workstation_nominal_step():
    ws = Workstation(
        station_id="station01",
        station_name="Cutting",
        base_rpm=1800.0,
        nominal_cycle_time=3.5,
        nominal_capacity=17.0,
        source="simulated",
    )
    ws.queue_length = 10
    # Advance by 4.0 seconds (sufficient time to complete >1 part)
    out = ws.step(input_units=0.0, dt_sec=4.0)
    assert out > 0.0
    assert ws.queue_length < 10
    assert ws.status == "NORMAL"
    telemetry = ws.to_telemetry()
    assert telemetry.rpm > 1700.0
    assert telemetry.station_id == "station01"


def test_workstation_stoppage():
    ws = Workstation(
        station_id="station02",
        station_name="Drilling",
        base_rpm=1500.0,
        nominal_cycle_time=4.0,
        nominal_capacity=15.0,
    )
    ws.current_rpm = 0.0
    ws.target_rpm = 0.0
    ws.queue_length = 5
    out = ws.step(input_units=2.0, dt_sec=1.0)
    assert out == 0.0
    assert ws.status == "STOPPED"
    assert ws.queue_length == 7


def test_factory_simulator_scenarios():
    sim = FactorySimulator()
    sim.set_scenario("scenario_a")
    step_a = sim.step(dt_override=1.0)
    assert "station01" in step_a
    assert "station02" in step_a
    assert "station03" in step_a
    assert "processed" in step_a

    # Test slowdown scenario
    sim.set_scenario("scenario_b")
    for _ in range(5):
        sim.step(dt_override=2.0)
    assert sim.station2.target_rpm < config.STATION2_BASE_RPM

    # Test reset
    sim.reset()
    assert sim.station2.current_rpm == config.STATION2_BASE_RPM
    assert sim.active_scenario == "scenario_a"
