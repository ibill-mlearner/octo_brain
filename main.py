"""Runnable entrypoint for the spatial-memory node-role prototype."""

import torch

from node_roles import NodeRoleServer
from tentacles.spatial_memory_system import SpatialMemorySystem


def main() -> None:
    """Run a small sensor-first walkthrough before debugging downstream roles."""
    torch.manual_seed(0)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    core = SpatialMemorySystem(
        channels=8,
        field_size=(100, 100, 100),
        window_size=(10, 10, 10),
        movement_mode="learned",
    ).to(device)

    roles = NodeRoleServer(core)
    sensor = roles.connect("sensor", node_id="sensor-1")

    print("Sensor-first walkthrough: 10 steps")
    print("Each step shows the raw roll-like value sent into the sensor node, then the sensor outcome.")

    for step in range(1, 11):
        roll_input = (step - 5.5) / 5.0
        sensor_frame = torch.zeros_like(sensor.active_state)
        sensor_frame[:, 0] = roll_input
        sensor_frame[:, 1] = -roll_input

        sensor.ingest_raw_values(sensor_frame)
        patch, prediction = sensor.sense_and_predict()
        error = float((prediction - patch).pow(2).mean().detach().item())

        sensor_roll_state = float(sensor.active_state[:, 0].mean().detach().item())
        sensor_counter_state = float(sensor.active_state[:, 1].mean().detach().item())
        patch_mean = float(patch.mean().detach().item())
        prediction_mean = float(prediction.mean().detach().item())

        print(
            f"step={step:02d} "
            f"sensor_input.roll={roll_input:+.3f} "
            f"sensor_input.counter_roll={-roll_input:+.3f} | "
            f"sensor_outcome.active_roll={sensor_roll_state:+.3f} "
            f"sensor_outcome.active_counter_roll={sensor_counter_state:+.3f} "
            f"sensor_outcome.patch_mean={patch_mean:+.5f} "
            f"sensor_outcome.prediction_mean={prediction_mean:+.5f} "
            f"sensor_outcome.prediction_error={error:.5f}"
        )


if __name__ == "__main__":
    main()
