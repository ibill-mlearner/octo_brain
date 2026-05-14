"""
Spatial memory demo wrapper around the standalone desktop sensor probe.

The top-level ``sensors`` package owns raw desktop readings. This prototype file
keeps the AI-specific step: normalize those raw values into a local spatial
frame with ``SpatialTokenizer`` for experiments.
"""

from __future__ import annotations

import argparse
import platform
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sensors.interfaces import SensorReading, collect_readings, readings_to_spatial_values
from tentacles.tokenizer import SpatialTokenizer


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe desktop counters and map them into one spatial sensor frame.")
    parser.add_argument("--samples", type=int, default=5, help="number of polling loops to print")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between polling loops")
    args = parser.parse_args()

    tokenizer = SpatialTokenizer(window_size=(10, 10, 10), add_eos=False)
    print(f"desktop_sensor_probe platform={platform.platform()}")

    for sample_index in range(args.samples):
        readings: list[SensorReading] = collect_readings()
        if not readings:
            print("no desktop readings available from the current OS/runtime")
            return

        values = readings_to_spatial_values(readings)
        frames = tokenizer.raw_values_to_frames(values, origins=[(0, 0, 0)], min_value=0.0, max_value=max(max(values), 1.0))
        frame = frames[0]
        print(f"sample={sample_index} readings={len(readings)} spatial_values={frame.values}")
        for reading in readings:
            suffix = f" {reading.unit}" if reading.unit else ""
            print(f"  {reading.name}: {reading.value:.4f}{suffix}")
        if sample_index + 1 < args.samples:
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
