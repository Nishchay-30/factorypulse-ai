"""
FactoryPulse AI - Simulation Daemon & Telemetry Publisher
Continuously advances factory model and publishes MQTT messages.
"""

import time
import signal
import logging
import argparse
from typing import Dict, Any

from src.common.config import config
from src.simulator.factory_simulator import FactorySimulator
from src.mqtt.client import MQTTClientWrapper
from src.mqtt.broker import broker_manager

logger = logging.getLogger("FactoryPulse.Runner")
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL), format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class SimulationRunner:
    """Orchestrates simulation execution and MQTT publication."""

    def __init__(self, scenario: str = config.DEFAULT_SCENARIO, time_scale: float = config.SIMULATION_TIME_SCALE):
        self.simulator = FactorySimulator()
        self.simulator.time_scale = time_scale
        self.simulator.set_scenario(scenario)
        self.running = False

        # Ensure broker is active if in local mode
        if config.MQTT_MODE == "local":
            broker_manager.ensure_broker_running()

        # Connect MQTT client
        self.mqtt_client = MQTTClientWrapper(
            client_id_suffix="simulator",
            on_message_callback=self._handle_incoming_command,
        )

    def _handle_incoming_command(self, topic: str, payload: Dict[str, Any]):
        """Respond to motor commands or simulation control messages."""
        logger.info("Simulator received message on %s: %s", topic, payload)
        if topic == config.TOPIC_MOTOR_COMMANDS:
            action = payload.get("action", "").upper()
            if action == "SET_SPEED":
                target_rpm = payload.get("target_rpm")
                speed_pwm = payload.get("speed_pwm")
                if target_rpm is not None:
                    self.simulator.station2.target_rpm = float(target_rpm)
                elif speed_pwm is not None:
                    # Calibration: 0-255 PWM -> 0-2000 RPM
                    calc_rpm = (float(speed_pwm) / 255.0) * config.STATION2_BASE_RPM
                    self.simulator.station2.target_rpm = calc_rpm
            elif action == "STOP":
                self.simulator.station2.target_rpm = 0.0
                self.simulator.station2.current_rpm = 0.0
            elif action == "START":
                self.simulator.station2.target_rpm = config.STATION2_BASE_RPM
            elif action == "RESET_ALARM":
                self.simulator.reset()

    def start(self, max_iterations: int = 0):
        """Start simulation publishing loop."""
        self.mqtt_client.connect(timeout=5.0)
        self.mqtt_client.subscribe(config.TOPIC_MOTOR_COMMANDS)
        self.running = True
        iteration = 0

        logger.info("Factory Simulator started. Publishing to MQTT topics...")

        try:
            while self.running:
                step_data = self.simulator.step()

                # Publish telemetry to station topics
                self.mqtt_client.publish(config.TOPIC_STATION1, step_data["station01"].model_dump())
                self.mqtt_client.publish(config.TOPIC_STATION2, step_data["station02"].model_dump())
                self.mqtt_client.publish(config.TOPIC_STATION3, step_data["station03"].model_dump())
                self.mqtt_client.publish(config.TOPIC_PROCESSED, step_data["processed"].model_dump())

                iteration += 1
                if max_iterations > 0 and iteration >= max_iterations:
                    break

                time.sleep(config.SIMULATION_INTERVAL_SEC)
        except KeyboardInterrupt:
            logger.info("Stopping simulation runner...")
        finally:
            self.stop()

    def stop(self):
        """Clean shutdown."""
        self.running = False
        self.mqtt_client.disconnect()
        logger.info("Factory Simulator stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FactoryPulse AI Simulation Runner")
    parser.add_argument("--scenario", default=config.DEFAULT_SCENARIO, help="Scenario key (scenario_a to scenario_f)")
    parser.add_argument("--scale", type=float, default=config.SIMULATION_TIME_SCALE, help="Time acceleration multiplier")
    parser.add_argument("--count", type=int, default=0, help="Maximum iterations (0 for infinite)")
    args = parser.parse_args()

    runner = SimulationRunner(scenario=args.scenario, time_scale=args.scale)

    def handle_signal(sig, frame):
        runner.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    runner.start(max_iterations=args.count)

