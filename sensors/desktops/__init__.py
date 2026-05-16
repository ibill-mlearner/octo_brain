"""Desktop sensor package exports.

This package initializer is the public doorway for desktop-specific sensor collection classes and helpers. It imports class implementations from their focused files so callers do not need to know the internal file layout. It also exposes the station accessor and compatibility helper functions that reuse stationed sensor objects. The initializer should stay light and should not contain probing, polling, or platform-specific collection logic. Keeping it as an export surface makes the desktop package easier to reorganize without breaking downstream imports.
"""

from __future__ import annotations

from .desktop_sensor import DesktopSensor
from .desktop_sensor_station import (
    DesktopSensorStation,
    get_default_desktop_sensor_station,
    collect_readings,
    fallback_readings,
    psutil_readings,
    readings_to_spatial_values,
    windows_readings,
)
from .fallback_sensor import DesktopFallbackSensor
from .psutil_sensor import DesktopPsutilSensor
from .windows_sensor import WindowsDesktopSensor


__all__ = [
    "DesktopFallbackSensor",
    "DesktopPsutilSensor",
    "DesktopSensor",
    "DesktopSensorLiveChart",
    "DesktopSensorStation",
    "WindowsDesktopSensor",
    "get_default_desktop_sensor_station",
    "collect_readings",
    "fallback_readings",
    "psutil_readings",
    "readings_to_spatial_values",
    "windows_readings",
]


def __getattr__(name: str) -> object:
    """Load optional charting support only when callers ask for it."""

    if name == "DesktopSensorLiveChart":
        from .charting import DesktopSensorLiveChart

        return DesktopSensorLiveChart
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

