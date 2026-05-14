"""
Public interface layer for the sensors package.

Python usually represents Java/C++-style interfaces with ``typing.Protocol``:
callers type against the method shape they need, while concrete classes can live
in smaller implementation files. External code should import sensor classes,
helpers, and protocols from this file instead of reaching into ``tokenizer.py``,
``scanner_environment.py``, or ``desktop_sensor_probe.py`` directly.
"""

from __future__ import annotations

from typing import Iterable, List, Protocol, Sequence, Tuple, runtime_checkable

from .desktop_sensor_probe import SensorReading, collect_readings, fallback_readings, readings_to_spatial_values, windows_readings
from .scanner_environment import Coordinate, ScannerConfig, ScannerEnvironment
from .tokenizer import ScanFrame, SensorFrame, SpatialTokenizer, WindowSize


@runtime_checkable
class SensorReader(Protocol):
    """Interface for an object that returns raw numeric sensor readings."""

    def collect_readings(self) -> List[SensorReading]:
        """Return the current raw readings as SensorReading objects."""


class DefaultSensorReader:
    """Concrete SensorReader that uses the platform-appropriate probe."""

    def collect_readings(self) -> List[SensorReading]:
        return collect_readings()


class FallbackSensorReader:
    """Concrete SensorReader that always uses standard-library fallback probes."""

    def collect_readings(self) -> List[SensorReading]:
        return fallback_readings()


class WindowsSensorReader:
    """Concrete SensorReader that asks Windows performance counters directly."""

    def collect_readings(self) -> List[SensorReading]:
        return windows_readings()


@runtime_checkable
class RawValueProjector(Protocol):
    """Interface for converting named readings into plain numeric streams."""

    def readings_to_spatial_values(self, readings: Iterable[SensorReading]) -> List[float]:
        """Return numeric values in the order they should enter spatial placement."""


class SensorValueProjector:
    """Concrete RawValueProjector that strips labels and units from readings."""

    def readings_to_spatial_values(self, readings: Iterable[SensorReading]) -> List[float]:
        return readings_to_spatial_values(readings)


@runtime_checkable
class ScannerNavigator(Protocol):
    """Interface for scanner movement over a 3D spatial field."""

    position: Coordinate
    visited: List[Coordinate]

    def clamp(self, position: Coordinate) -> Coordinate:
        """Return a scanner origin clipped to the legal field bounds."""

    def move(self, delta: Coordinate) -> Coordinate:
        """Move relative to the current scanner origin and return the new origin."""

    def move_to(self, position: Coordinate) -> Coordinate:
        """Jump to an absolute scanner origin and return the new origin."""

    def path_to(self, goal: Coordinate, step: Coordinate | None = None) -> List[Coordinate]:
        """Return an axis-aligned path from the current origin to a goal."""

    def follow(self, path: Iterable[Coordinate]) -> Coordinate:
        """Move through a path and return the final origin."""

    def raster_scan(self, serpentine: bool = True) -> List[Coordinate]:
        """Return every scanner origin needed to cover the configured field."""


@runtime_checkable
class SpatialFramePlacer(Protocol):
    """Interface for placing raw values or debug text into scanner frames."""

    window_size: WindowSize
    add_eos: bool

    @property
    def window_volume(self) -> int:
        """Return the number of cells in one scanner window."""

    def encode(self, text: str) -> List[int]:
        """Encode debug text into reversible byte-level token IDs."""

    def decode(self, token_ids: Iterable[int], stop_at_eos: bool = True) -> str:
        """Decode debug token IDs back into text."""

    def normalize_raw_values(self, values: Iterable[float], min_value: float = 0.0, max_value: float = 255.0) -> List[float]:
        """Clip and scale raw sensor values into the 0..1 range."""

    def chunk(self, values: Sequence[float | int]) -> List[Tuple[float | int, ...]]:
        """Split values into scanner-window-sized chunks."""

    def local_coordinate(self, local_index: int) -> Coordinate:
        """Return the local x/y/z coordinate for a flat window index."""

    def coordinates_for_count(self, origin: Coordinate, count: int) -> Tuple[Coordinate, ...]:
        """Return absolute coordinates for the first count cells at origin."""

    def token_coordinates(self, origin: Coordinate, count: int) -> Tuple[Coordinate, ...]:
        """Backward-compatible alias for coordinate placement."""

    def raw_values_to_frames(
        self,
        values: Sequence[float],
        origins: Sequence[Coordinate],
        min_value: float = 0.0,
        max_value: float = 255.0,
    ) -> List[SensorFrame]:
        """Place normalized raw values into one or more sensor frames."""

    def encode_to_frames(self, text: str, origins: Sequence[Coordinate]) -> List[ScanFrame]:
        """Place encoded debug text into one or more scan frames."""


__all__ = [
    "Coordinate",
    "DefaultSensorReader",
    "FallbackSensorReader",
    "RawValueProjector",
    "ScanFrame",
    "ScannerConfig",
    "ScannerEnvironment",
    "ScannerNavigator",
    "SensorFrame",
    "SensorReader",
    "SensorReading",
    "SensorValueProjector",
    "SpatialFramePlacer",
    "SpatialTokenizer",
    "WindowSize",
    "WindowsSensorReader",
    "collect_readings",
    "fallback_readings",
    "readings_to_spatial_values",
    "windows_readings",
]
