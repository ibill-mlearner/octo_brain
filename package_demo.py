"""
Root-level demo for the standalone sensors package.

This is intentionally a small package smoke demo, not a unit test. It imports
through the public interface layer and runs the concrete sensors package pieces
from the repository root:

    python package_demo.py
"""

from __future__ import annotations

from pprint import pprint

from sensors.interfaces import (
    DefaultSensorReader,
    RawValueProjector,
    ScannerConfig,
    ScannerEnvironment,
    ScannerNavigator,
    SensorReader,
    SensorReading,
    SensorValueProjector,
)


def main() -> None:
    print("=== sensors package demo ===")

    reader: SensorReader = DefaultSensorReader()
    readings = reader.collect_readings()
    print(f"collected {len(readings)} runtime reading(s):")
    pprint(readings[:5])

    sample_readings = readings or [SensorReading("demo_signal", 42.0, "units")]
    projector: RawValueProjector = SensorValueProjector()
    raw_values = projector.readings_to_spatial_values(sample_readings)
    print("raw values for downstream placement:")
    pprint(raw_values[:5])

    scanner: ScannerNavigator = ScannerEnvironment(
        config=ScannerConfig(field_size=(20, 20, 10), window_size=(10, 10, 5), stride=(10, 10, 5))
    )
    scan_origins = scanner.raster_scan(serpentine=True)
    print("first scanner origins:")
    pprint(scan_origins[:5])

    print("spatial placement is intentionally outside sensors; see tokenizer.py")


if __name__ == "__main__":
    main()
