"""
Public interface layer for the sensors package.

Python usually represents Java/C++-style interfaces with ``typing.Protocol``:
callers type against the method shape they need, while concrete classes can live
in smaller implementation files. External code should import sensor classes,
helpers, and protocols from this file instead of reaching into
``tentacles.scanner_environment`` or ``sensors.desktop_sensor_probe`` directly.
"""

from __future__ import annotations

from typing import Iterable, List, Protocol, runtime_checkable

from .desktop_sensor_probe import SensorReading, collect_readings, fallback_readings, psutil_readings, readings_to_spatial_values, windows_readings
from tentacles.scanner_environment import Coordinate, ScannerConfig, ScannerEnvironment
from tentacles.tokenizer import ScanFrame, SensorFrame, SpatialTokenizer


@runtime_checkable
class SensorReader(Protocol):
    """Interface for an object that returns raw numeric sensor readings."""

    def collect_readings(self) -> List[SensorReading]:
        """Return the current raw readings as SensorReading objects."""


class DefaultSensorReader:
    """Concrete SensorReader that uses the best available desktop probe."""

    def collect_readings(self) -> List[SensorReading]:
        return collect_readings()


class FallbackSensorReader:
    """Concrete SensorReader that always uses standard-library fallback probes."""

    def collect_readings(self) -> List[SensorReading]:
        return fallback_readings()


class WindowsSensorReader:
    """Concrete SensorReader that uses Python desktop probes on Windows."""

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


__all__ = [
    "Coordinate",
    "DefaultSensorReader",
    "FallbackSensorReader",
    "RawValueProjector",
    "ScannerConfig",
    "ScannerEnvironment",
    "ScanFrame",
    "ScannerNavigator",
    "SensorFrame",
    "SensorReader",
    "SensorReading",
    "SensorValueProjector",
    "SpatialTokenizer",
    "WindowsSensorReader",
    "collect_readings",
    "fallback_readings",
    "psutil_readings",
    "readings_to_spatial_values",
    "windows_readings",
]
