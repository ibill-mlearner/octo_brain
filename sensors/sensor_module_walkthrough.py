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
    ScanFrame,
    ScannerConfig,
    ScannerEnvironment,
    ScannerNavigator,
    SensorFrame,
    SensorReader,
    SensorReading,
    SensorValueProjector,
    SpatialFramePlacer,
    SpatialTokenizer,
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

# WindowsSensorReader implements SensorReader by asking Windows performance
# counters directly.
# Demo:
#     windows_reader.collect_readings()
# Expected behavior: on Windows, returns CPU/memory/disk/thermal/fan counters the
# OS exposes. On non-Windows systems or when PowerShell is absent, it returns an
# empty list instead of crashing.
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
# Raw value tokenizer and frame placement
# ---------------------------------------------------------------------------

# SpatialTokenizer maps raw numeric streams or debug text into scanner-window
# coordinates. add_eos controls only the debug text path.
tokenizer: SpatialFramePlacer = SpatialTokenizer(window_size=(2, 2, 1), add_eos=True)

# SpatialTokenizer.window_volume
# Demo:
#     tokenizer.window_volume
# Expected behavior: multiplies the three window dimensions. A (2,2,1) window
# can hold four samples per frame.
window_volume = tokenizer.window_volume

# normalize_raw_values(values, min_value=0.0, max_value=255.0)
# Demo:
#     tokenizer.normalize_raw_values([-10, 0, 127.5, 255, 999])
# Expected behavior: clips values into the min/max range, then scales to 0..1.
normalized_values = tokenizer.normalize_raw_values([-10, 0, 127.5, 255, 999])

# chunk(values)
# Demo:
#     tokenizer.chunk([0, 1, 2, 3, 4])
# Expected behavior: splits a sequence into frame-sized tuples. With volume 4,
# this returns [(0,1,2,3), (4,)].
chunks = tokenizer.chunk([0, 1, 2, 3, 4])

# local_coordinate(local_index)
# Demo:
#     tokenizer.local_coordinate(3)
# Expected behavior: converts a flat index inside the local scanner window into
# x-then-y-then-z coordinates. Index 3 in a (2,2,1) window is (1,1,0).
local_coord = tokenizer.local_coordinate(3)

# coordinates_for_count(origin, count)
# Demo:
#     tokenizer.coordinates_for_count((10, 20, 30), 3)
# Expected behavior: returns absolute coordinates for the first count local
# positions added to origin: ((10,20,30), (11,20,30), (10,21,30)).
absolute_coords = tokenizer.coordinates_for_count((10, 20, 30), 3)

# token_coordinates(origin, count)
# Demo:
#     tokenizer.token_coordinates((10, 20, 30), 3)
# Expected behavior: same as coordinates_for_count; this name remains for older
# text/debug callers.
token_coords = tokenizer.token_coordinates((10, 20, 30), 3)

# raw_values_to_frames(values, origins, min_value=0.0, max_value=255.0)
# Demo:
#     tokenizer.raw_values_to_frames([0, 127.5, 255, 64, 32], [(0,0,0), (10,0,0)])
# Expected behavior: normalizes the raw numbers, chunks by window volume, and
# returns SensorFrame objects carrying origin, window size, normalized values,
# and absolute coordinates.
sensor_frames = tokenizer.raw_values_to_frames([0, 127.5, 255, 64, 32], origins=[(0, 0, 0), (10, 0, 0)])

# encode(text)
# Demo:
#     tokenizer.encode("hi")
# Expected behavior: UTF-8 bytes are offset above special-token IDs; because
# add_eos=True, the sequence ends with SpatialTokenizer.EOS.
token_ids = tokenizer.encode("hi")

# decode(token_ids, stop_at_eos=True)
# Demo:
#     tokenizer.decode(token_ids)
# Expected behavior: reverses encode() back to text and stops at EOS by default.
# Padding/unknown/special IDs are ignored.
decoded_text = tokenizer.decode(token_ids)

# encode_to_frames(text, origins)
# Demo:
#     tokenizer.encode_to_frames("hello", [(0,0,0), (10,0,0)])
# Expected behavior: encodes debug text, chunks token IDs by window volume, and
# returns ScanFrame objects with token IDs and coordinates. This is only a debug
# convenience; raw sensors should use raw_values_to_frames().
scan_frames = tokenizer.encode_to_frames("hello", origins=[(0, 0, 0), (10, 0, 0)])

# ScanFrame can also be instantiated directly if a caller already has token IDs
# and coordinates. Expected behavior: stores the provided debug/text token frame
# exactly as passed.
manual_scan_frame = ScanFrame(
    origin=(0, 0, 0),
    window_size=(2, 2, 1),
    token_ids=(SpatialTokenizer.BYTE_OFFSET + ord("x"), SpatialTokenizer.EOS),
    coordinates=((0, 0, 0), (1, 0, 0)),
)

# SensorFrame can also be instantiated directly if a caller already has raw
# normalized values and coordinates. Expected behavior: stores one raw numeric
# sensor frame exactly as passed.
manual_sensor_frame = SensorFrame(
    origin=(0, 0, 0),
    window_size=(2, 2, 1),
    values=(0.0, 0.5, 1.0),
    coordinates=((0, 0, 0), (1, 0, 0), (0, 1, 0)),
)


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
    print("tokenizer window_volume:", window_volume)
    print("normalized_values:", normalized_values)
    print("chunks:", chunks)
    print("local/absolute/token coords:", local_coord, absolute_coords, token_coords)
    print("sensor_frames:")
    pprint(sensor_frames)
    print("token_ids/decoded_text:", token_ids, decoded_text)
    print("scan_frames:")
    pprint(scan_frames)
    print("manual frames:")
    pprint([manual_scan_frame, manual_sensor_frame])


if __name__ == "__main__":
    main()
