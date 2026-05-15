"""Command-line wrapper for desktop raw-number sensor probes.

This file is the runnable entry point for printing desktop sensor readings from the terminal. The actual collection logic lives in ``sensors.desktops`` so this wrapper stays small and easy to inspect. It preserves the legacy helper exports for callers that still import from ``desktop_sensor_probe``. The command-line loop only formats samples, raw values, and units for human-readable output. It does not normalize readings, group readings, or perform spatial-memory placement.
"""

from __future__ import annotations

import argparse
import platform
import time

from models.sensors import SensorReading

from .desktops import (
    collect_readings,
    fallback_readings,
    psutil_readings,
    readings_to_spatial_values,
    windows_readings,
)


__all__ = [
    "SensorReading",
    "collect_readings",
    "fallback_readings",
    "main",
    "psutil_readings",
    "readings_to_spatial_values",
    "windows_readings",
]


def main() -> None:
    """Run the desktop sensor probe as a small command-line printer.

    The function parses sample-count and delay arguments, then delegates every collection pass to the desktop sensor package helpers.
    """

    parser = argparse.ArgumentParser(
        description="Probe desktop counters as raw numeric sensor readings."
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=5,
        help="number of polling loops to print",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="seconds between polling loops",
    )
    args = parser.parse_args()

    print(f"desktop_sensor_probe platform={platform.platform()}")

    for sample_index in range(args.samples):
        readings = collect_readings()
        if not readings:
            print("no desktop readings available from the current OS/runtime")
            return

        values = readings_to_spatial_values(readings)
        print(f"sample={sample_index} readings={len(readings)} raw_values={values}")
        for reading in readings:
            suffix = f" {reading.unit}" if reading.unit else ""
            print(f"  {reading.name}: {reading.value:.4f}{suffix}")
        if sample_index + 1 < args.samples:
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
