"""
Standalone desktop raw-number probe for early sensor experiments.

Run this file directly on a desktop. On Windows it asks PowerShell for common
performance counters that are usually available without installing extra Python
packages. Hardware temperature/fan counters are vendor/driver dependent, so the
probe reports them when Windows exposes them and otherwise keeps going.

This is intentionally not wired into the model yet. It just collects constantly
changing numbers, normalizes them with SpatialTokenizer, and prints the first
spatial frame so we have real-ish raw values to experiment with.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import time
from dataclasses import dataclass
from typing import Iterable, List

from .tokenizer import SpatialTokenizer


@dataclass(frozen=True)
class SensorReading:
    name: str
    value: float
    unit: str = ""


WINDOWS_COUNTER_SCRIPT = r"""
$ErrorActionPreference = 'SilentlyContinue'
$readings = @()
$counters = @(
    '\Processor(_Total)\% Processor Time',
    '\Memory\Available MBytes',
    '\System\Processor Queue Length',
    '\PhysicalDisk(_Total)\% Disk Time'
)
foreach ($counterPath in $counters) {
    try {
        $sample = Get-Counter -Counter $counterPath -SampleInterval 1 -MaxSamples 1
        foreach ($counter in $sample.CounterSamples) {
            $readings += [pscustomobject]@{
                name = $counter.Path
                value = [double]$counter.CookedValue
                unit = 'counter'
            }
        }
    } catch {}
}
try {
    $temps = Get-WmiObject -Namespace root/wmi -Class MSAcpi_ThermalZoneTemperature
    foreach ($temp in $temps) {
        $celsius = ([double]$temp.CurrentTemperature / 10.0) - 273.15
        $readings += [pscustomobject]@{
            name = 'MSAcpi_ThermalZoneTemperature'
            value = $celsius
            unit = 'C'
        }
    }
} catch {}
try {
    $fans = Get-WmiObject -Class Win32_Fan
    foreach ($fan in $fans) {
        if ($null -ne $fan.DesiredSpeed) {
            $readings += [pscustomobject]@{
                name = 'Win32_Fan.DesiredSpeed'
                value = [double]$fan.DesiredSpeed
                unit = 'rpm'
            }
        }
    }
} catch {}
$readings | ConvertTo-Json -Depth 3
"""


def windows_readings() -> List[SensorReading]:
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", WINDOWS_COUNTER_SCRIPT],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    if result.returncode != 0 or not result.stdout.strip():
        return []

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if isinstance(payload, dict):
        payload = [payload]

    readings = []
    for item in payload:
        try:
            readings.append(SensorReading(name=str(item["name"]), value=float(item["value"]), unit=str(item.get("unit", ""))))
        except (KeyError, TypeError, ValueError):
            continue
    return readings


def fallback_readings() -> List[SensorReading]:
    readings = []
    if hasattr(os, "getloadavg"):
        for label, value in zip(("load_1m", "load_5m", "load_15m"), os.getloadavg()):
            readings.append(SensorReading(label, float(value), "load"))
    readings.append(SensorReading("process_time", time.process_time(), "seconds"))
    return readings


def collect_readings() -> List[SensorReading]:
    if platform.system().lower() == "windows":
        readings = windows_readings()
        if readings:
            return readings
    return fallback_readings()


def readings_to_spatial_values(readings: Iterable[SensorReading]) -> List[float]:
    # Keep this deliberately simple: these are raw-ish changing numbers. The
    # tokenizer clamps/normalizes for spatial placement after collection.
    return [reading.value for reading in readings]


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe desktop counters and map them into one spatial sensor frame.")
    parser.add_argument("--samples", type=int, default=5, help="number of polling loops to print")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between polling loops")
    args = parser.parse_args()

    tokenizer = SpatialTokenizer(window_size=(10, 10, 10), add_eos=False)
    print(f"desktop_sensor_probe platform={platform.platform()}")

    for sample_index in range(args.samples):
        readings = collect_readings()
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
