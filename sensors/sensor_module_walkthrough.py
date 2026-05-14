"""
Readable walkthrough for the ``sensors`` module.

This file is intentionally not a unit test. It is a runnable/readable reference
that instantiates every concrete sensor class and routes access through the
interface layer. Comments show how each public method or helper is expected to
behave.

Run from the repository root if you want to see the concrete demo values:

    python -m sensors.sensor_module_walkthrough
"""

from __future__ import annotations

from pprint import pprint

from .interfaces import (
    DefaultSensorReader,
    FallbackSensorReader,
    RawValueProjector,
    ScannerConfig,
    ScannerEnvironment,
    ScannerNavigator,
    SensorReader,
    SensorReading,
    SensorValueProjector,
    WindowsSensorReader,
)


# ---------------------------------------------------------------------------
# Desktop sensor readings
# ---------------------------------------------------------------------------

# SensorReading is the small raw sample container used by desktop probes.
# Expected behavior: the constructor stores a name, numeric value, and optional
# unit without changing the value. It is frozen, so callers cannot accidentally
# mutate a reading after collection.
cpu_reading = SensorReading(name="cpu_percent", value=37.5, unit="%")
memory_reading = SensorReading(name="available_memory", value=2048.0, unit="MB")

# SensorValueProjector implements the RawValueProjector interface.
# Demo:
#     value_projector.readings_to_spatial_values([cpu_reading, memory_reading])
# Expected behavior: returns only the raw numeric values in the same order,
# because the tokenizer/scanner placement layer should consume numbers rather
# than semantic labels.
value_projector: RawValueProjector = SensorValueProjector()
raw_values = value_projector.readings_to_spatial_values([cpu_reading, memory_reading])

# FallbackSensorReader implements the SensorReader interface with only
# standard-library probes.
# Demo:
#     fallback_reader.collect_readings()
# Expected behavior: returns values that exist on this runtime, such as
# process_time and, when available, load averages.
fallback_reader: SensorReader = FallbackSensorReader()
fallback_demo_readings = fallback_reader.collect_readings()

# WindowsSensorReader implements SensorReader by using the optional psutil
# Python package on Windows.
# Demo:
#     windows_reader.collect_readings()
# Expected behavior: on Windows with psutil installed, returns CPU, memory,
# disk, network, battery, thermal, and fan values exposed by the OS/package.
# On non-Windows systems, or without psutil, it returns an empty list instead
# of crashing.
windows_reader: SensorReader = WindowsSensorReader()
windows_demo_readings = windows_reader.collect_readings()

# DefaultSensorReader implements SensorReader with platform selection.
# Demo:
#     default_reader.collect_readings()
# Expected behavior: on Windows it first tries WindowsSensorReader behavior; if
# counters are unavailable, or on other operating systems, it falls back to the
# standard-library readings. This is the reader most callers should use.
default_reader: SensorReader = DefaultSensorReader()
collected_demo_readings = default_reader.collect_readings()


# ---------------------------------------------------------------------------
# Scanner movement environment
# ---------------------------------------------------------------------------

# ScannerConfig configures the 3D field, local window, and movement stride.
scanner_config = ScannerConfig(field_size=(30, 20, 10), window_size=(10, 10, 5), stride=(10, 5, 5))

# ScannerConfig.max_origin
# Demo:
#     scanner_config.max_origin
# Expected behavior: returns the largest legal scanner origin for each axis.
# With field_size=(30,20,10) and window_size=(10,10,5), max_origin is
# (20, 10, 5). A scanner origin beyond this would place part of the window
# outside the memory field.
max_origin = scanner_config.max_origin

# ScannerEnvironment owns current scanner position and a visited-position log.
# __post_init__ runs after dataclass construction.
# Demo:
#     ScannerEnvironment(config=scanner_config, position=(99, -1, 3))
# Expected behavior: __post_init__ clamps the initial position into the legal
# field and appends that starting position to visited.
scanner: ScannerNavigator = ScannerEnvironment(config=scanner_config, position=(99, -1, 3))

# clamp(position)
# Demo:
#     scanner.clamp((999, -5, 99))
# Expected behavior: clips every axis to the inclusive range from 0 through
# config.max_origin, returning (20, 0, 5) for this config.
clamped_position = scanner.clamp((999, -5, 99))

# move(delta)
# Demo:
#     scanner.move((-5, 5, 99))
# Expected behavior: adds delta to the current position, clamps the result,
# stores it as scanner.position, records it in visited, and returns it.
moved_position = scanner.move((-5, 5, 99))

# move_to(position)
# Demo:
#     scanner.move_to((10, 5, 0))
# Expected behavior: clamps and jumps directly to the requested origin, records
# that origin in visited, and returns the new position.
absolute_position = scanner.move_to((10, 5, 0))

# path_to(goal, step=None)
# Demo:
#     scanner.path_to((20, 10, 5), step=(10, 5, 5))
# Expected behavior: builds an axis-aligned path from the current position to
# the clamped goal. It moves x first, then y, then z. It does not mutate the
# scanner until follow(path) is called.
path = scanner.path_to((20, 10, 5), step=(10, 5, 5))

# follow(path)
# Demo:
#     scanner.follow(path)
# Expected behavior: calls move_to for every point in the path, so position and
# visited are updated. It returns the final position.
followed_position = scanner.follow(path)

# raster_scan(serpentine=True)
# Demo:
#     scanner.raster_scan()
# Expected behavior: returns every legal window origin at stride intervals. With
# serpentine=True, x direction alternates by row/plane so consecutive origins are
# closer together than a naive left-to-right reset every row.
raster_path = scanner.raster_scan(serpentine=True)


# ---------------------------------------------------------------------------
# Spatial placement moved out of sensors
# ---------------------------------------------------------------------------

# Tokenizer/frame placement code is intentionally not demonstrated here anymore.
# The sensors package should expose raw desktop readings and scanner movement
# primitives only; AI-specific spatial placement now lives in
# spatial_memory_proto/tokenizer.py.


def main() -> None:
    """Print the walkthrough's concrete values without asserting anything."""

    print("SensorReading values:")
    pprint([cpu_reading, memory_reading])
    print("raw_values:", raw_values)
    print("fallback_demo_readings sample:", fallback_demo_readings[:3])
    print("windows_demo_readings sample:", windows_demo_readings[:3])
    print("collected_demo_readings sample:", collected_demo_readings[:3])
    print("scanner max_origin:", max_origin)
    print("scanner clamped/moved/absolute/followed:", clamped_position, moved_position, absolute_position, followed_position)
    print("scanner path:", path)
    print("raster first five:", raster_path[:5])
    print("spatial placement:", "see spatial_memory_proto/tokenizer.py")


if __name__ == "__main__":
    main()
