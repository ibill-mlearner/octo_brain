"""
Public interface layer for the sensors package.

This module is the stable import surface for callers that need sensor readers, raw-value projection, scanner navigation, or related concrete helpers. Python usually represents Java/C++-style interfaces with ``typing.Protocol``: callers type against the method shape they need, while concrete classes can live in smaller implementation files. External code should import sensor classes, helpers, and protocols from this file instead of reaching into ``tentacles.scanner_environment`` or ``sensors.desktop_sensor_probe`` directly. The file intentionally re-exports selected desktop sensor classes so callers can use them without depending on the package layout under ``sensors.desktops``. It should remain a public wiring layer rather than a place for collection logic or spatial-memory behavior.
"""

from __future__ import annotations

from typing import Iterable, List, Protocol, runtime_checkable

from models.sensors import SensorReading

from .base_sensor import BaseSensor
from .desktops import (
    DesktopFallbackSensor,
    DesktopPsutilSensor,
    DesktopSensor,
    WindowsDesktopSensor,
    collect_readings,
    fallback_readings,
    psutil_readings,
    readings_to_spatial_values,
    windows_readings,
)
from .sensor_results_collector import SensorResultsCollector
from tentacles.scanner_environment import Coordinate, ScannerConfig, ScannerEnvironment
from tentacles.tokenizer import ScanFrame, SensorFrame, SpatialTokenizer


@runtime_checkable
class SensorReader(Protocol):
    """Interface for an object that returns raw numeric sensor readings."""

    def collect_readings(self) -> List[SensorReading]:
        """Return the current raw readings as ``SensorReading`` objects.

        Implementations may use any collection source as long as they preserve this simple list-returning contract.
        """


class DefaultSensorReader(DesktopSensor):
    """Concrete SensorReader that uses the best available desktop probe."""


class FallbackSensorReader(DesktopFallbackSensor):
    """Concrete SensorReader that always uses standard-library fallback probes."""


class WindowsSensorReader(WindowsDesktopSensor):
    """Concrete SensorReader that uses Python desktop probes on Windows."""


@runtime_checkable
class RawValueProjector(Protocol):
    """Interface for converting named readings into plain numeric streams."""

    def readings_to_spatial_values(
        self,
        readings: Iterable[SensorReading],
    ) -> List[float]:
        """Return numeric values in the order they should enter spatial placement.

        Projectors keep the conversion from named readings to plain value streams explicit for downstream callers.
        """


class SensorValueProjector:
    """Concrete RawValueProjector that strips labels and units from readings."""

    def readings_to_spatial_values(
        self,
        readings: Iterable[SensorReading],
    ) -> List[float]:
        """Return plain numeric values from named sensor readings.

        This concrete projector delegates to the package helper so interface users and helper users share the same projection behavior.
        """

        return readings_to_spatial_values(readings)


@runtime_checkable
class ScannerNavigator(Protocol):
    """Interface for scanner movement over a 3D spatial field."""

    position: Coordinate
    visited: List[Coordinate]

    def clamp(self, position: Coordinate) -> Coordinate:
        """Return a scanner origin clipped to the legal field bounds.

        Implementations should avoid mutating scanner state when they are only answering this bounds-checking question.
        """

    def move(self, delta: Coordinate) -> Coordinate:
        """Move relative to the current scanner origin and return the new origin.

        The protocol expects implementations to handle clamping, state updates, and visited-position tracking consistently.
        """

    def move_to(self, position: Coordinate) -> Coordinate:
        """Jump to an absolute scanner origin and return the new origin.

        Implementations should treat this as an absolute placement operation rather than a relative delta.
        """

    def path_to(
        self,
        goal: Coordinate,
        step: Coordinate | None = None,
    ) -> List[Coordinate]:
        """Return an axis-aligned path from the current origin to a goal.

        The method describes planning behavior and should not require the scanner to move until a caller follows the path.
        """

    def follow(self, path: Iterable[Coordinate]) -> Coordinate:
        """Move through a path and return the final origin.

        Implementations should apply the same movement and visited-position behavior they use for single moves.
        """

    def raster_scan(self, serpentine: bool = True) -> List[Coordinate]:
        """Return every scanner origin needed to cover the configured field.

        The returned path describes coverage order for scanning and leaves execution to the caller.
        """


__all__ = [
    "BaseSensor",
    "Coordinate",
    "DefaultSensorReader",
    "DesktopFallbackSensor",
    "DesktopPsutilSensor",
    "DesktopSensor",
    "FallbackSensorReader",
    "RawValueProjector",
    "ScannerConfig",
    "ScannerEnvironment",
    "ScanFrame",
    "ScannerNavigator",
    "SensorFrame",
    "SensorReader",
    "SensorReading",
    "SensorResultsCollector",
    "SensorValueProjector",
    "SpatialTokenizer",
    "WindowsDesktopSensor",
    "WindowsSensorReader",
    "collect_readings",
    "fallback_readings",
    "psutil_readings",
    "readings_to_spatial_values",
    "windows_readings",
]
