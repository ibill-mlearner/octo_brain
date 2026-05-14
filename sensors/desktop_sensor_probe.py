"""
Standalone desktop raw-number probe for early sensor experiments.

Run this file directly on a desktop. It prefers the Python ``psutil`` package
when installed, which gives us CPU, memory, disk, network, and battery readings
without shelling out to a handcrafted Windows/PowerShell counter script. If
``psutil`` is unavailable, the probe falls back to a tiny standard-library set
of process/load values so callers still receive safe numeric samples.

This module intentionally stops at raw readings. AI-specific placement into
spatial frames lives in the spatial memory prototype, not in the sensors package.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import os
import platform
import time
from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class SensorReading:
    name: str
    value: float
    unit: str = ""


def _psutil_module():
    """Return psutil when installed without making it mandatory for this repo."""
    if importlib.util.find_spec("psutil") is None:
        return None
    return importlib.import_module("psutil")


def psutil_readings() -> List[SensorReading]:
    """Collect desktop readings with psutil when that optional package exists."""
    psutil = _psutil_module()
    if psutil is None:
        return []

    readings: List[SensorReading] = []

    readings.append(SensorReading("cpu_percent", float(psutil.cpu_percent(interval=0.0)), "%"))

    memory = psutil.virtual_memory()
    readings.extend(
        [
            SensorReading("memory_available", float(memory.available), "bytes"),
            SensorReading("memory_used_percent", float(memory.percent), "%"),
        ]
    )

    disk_usage = psutil.disk_usage(os.getcwd())
    readings.append(SensorReading("disk_used_percent", float(disk_usage.percent), "%"))

    disk_io = psutil.disk_io_counters()
    if disk_io is not None:
        readings.extend(
            [
                SensorReading("disk_read_bytes", float(disk_io.read_bytes), "bytes"),
                SensorReading("disk_write_bytes", float(disk_io.write_bytes), "bytes"),
            ]
        )

    network_io = psutil.net_io_counters()
    if network_io is not None:
        readings.extend(
            [
                SensorReading("net_bytes_sent", float(network_io.bytes_sent), "bytes"),
                SensorReading("net_bytes_recv", float(network_io.bytes_recv), "bytes"),
            ]
        )

    battery = getattr(psutil, "sensors_battery", lambda: None)()
    if battery is not None:
        readings.append(SensorReading("battery_percent", float(battery.percent), "%"))
        if battery.secsleft not in (psutil.POWER_TIME_UNLIMITED, psutil.POWER_TIME_UNKNOWN):
            readings.append(SensorReading("battery_seconds_left", float(battery.secsleft), "seconds"))

    temperatures = getattr(psutil, "sensors_temperatures", lambda: {})()
    for sensor_name, entries in temperatures.items():
        for index, entry in enumerate(entries):
            if entry.current is not None:
                label = entry.label or str(index)
                readings.append(SensorReading(f"temperature_{sensor_name}_{label}", float(entry.current), "C"))

    fans = getattr(psutil, "sensors_fans", lambda: {})()
    for sensor_name, entries in fans.items():
        for index, entry in enumerate(entries):
            if entry.current is not None:
                label = entry.label or str(index)
                readings.append(SensorReading(f"fan_{sensor_name}_{label}", float(entry.current), "rpm"))

    return readings


def windows_readings() -> List[SensorReading]:
    """Return Windows desktop readings through the Python psutil path."""
    if platform.system().lower() != "windows":
        return []
    return psutil_readings()


def fallback_readings() -> List[SensorReading]:
    readings = []
    if hasattr(os, "getloadavg"):
        for label, value in zip(("load_1m", "load_5m", "load_15m"), os.getloadavg()):
            readings.append(SensorReading(label, float(value), "load"))
    readings.append(SensorReading("process_time", time.process_time(), "seconds"))
    return readings


def collect_readings() -> List[SensorReading]:
    readings = psutil_readings()
    if readings:
        return readings
    return fallback_readings()


def readings_to_spatial_values(readings: Iterable[SensorReading]) -> List[float]:
    # Keep this deliberately simple: these are raw-ish changing numbers. The
    # spatial memory placement layer can clamp/normalize after collection.
    return [reading.value for reading in readings]


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe desktop counters as raw numeric sensor readings.")
    parser.add_argument("--samples", type=int, default=5, help="number of polling loops to print")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between polling loops")
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
