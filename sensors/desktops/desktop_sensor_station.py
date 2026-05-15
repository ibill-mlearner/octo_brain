"""Persistent desktop sensor station and compatibility helpers.

This file owns the object that keeps desktop sensor instances stationed in memory across polling calls. The station is useful for loops that repeatedly gather readings and should not rebuild psutil, fallback, and selector objects every iteration. It also hosts the compatibility helper functions that older callers can use without directly managing a station instance. The helper functions route through a lazy process-local station, so they preserve a simple function API while still reusing sensor objects. This module intentionally contains orchestration and lifetime behavior, leaving concrete reading collection in the individual sensor class files.
"""

from __future__ import annotations

from typing import Iterable, List

from models.sensors import SensorReading

from .desktop_sensor import DesktopSensor
from .fallback_sensor import DesktopFallbackSensor
from .psutil_sensor import DesktopPsutilSensor
from .windows_sensor import WindowsDesktopSensor


class DesktopSensorStation:
    """Hold desktop sensor objects in memory between collection calls.

    The station coordinates object lifetime and delegates actual reading collection to the concrete sensor instances it owns.
    """

    def __init__(
        self,
        psutil_sensor: DesktopPsutilSensor | None = None,
        fallback_sensor: DesktopFallbackSensor | None = None,
        desktop_sensor: DesktopSensor | None = None,
        windows_sensor: WindowsDesktopSensor | None = None,
    ) -> None:
        """Create or accept the concrete sensor instances for this station.

        Optional injected sensors make the station easy to customize while the default path builds the standard psutil, fallback, desktop, and Windows sensors once.
        """

        self.psutil_sensor = psutil_sensor or DesktopPsutilSensor()
        self.fallback_sensor = fallback_sensor or DesktopFallbackSensor()
        self.desktop_sensor = desktop_sensor or DesktopSensor(
            psutil_sensor=self.psutil_sensor,
            fallback_sensor=self.fallback_sensor,
        )
        self.windows_sensor = windows_sensor or WindowsDesktopSensor()

    def psutil_readings(self) -> List[SensorReading]:
        """Collect desktop readings with the stationed psutil sensor.

        This method reuses the same psutil-backed sensor instance instead of constructing a new one for each call.
        """

        return self.psutil_sensor.collect_readings()

    def windows_readings(self) -> List[SensorReading]:
        """Collect Windows readings with the stationed Windows sensor.

        The Windows sensor owns its platform guard, so the station can safely delegate on any operating system.
        """

        return self.windows_sensor.collect_readings()

    def fallback_readings(self) -> List[SensorReading]:
        """Collect portable readings with the stationed fallback sensor.

        This provides direct access to the standard-library fallback path for callers that do not want psutil selection.
        """

        return self.fallback_sensor.collect_readings()

    def collect_readings(self) -> List[SensorReading]:
        """Collect readings with the stationed default desktop sensor.

        The default desktop sensor applies psutil-first and fallback-second selection while still using objects owned by this station.
        """

        return self.desktop_sensor.collect_readings()

    def readings_to_spatial_values(
        self,
        readings: Iterable[SensorReading],
    ) -> List[float]:
        """Return raw numeric values for downstream spatial placement.

        The helper keeps function-style projection compatible with callers that do not manage a station directly.
        """

        return self.desktop_sensor.readings_to_spatial_values(readings)


_DEFAULT_DESKTOP_SENSOR_STATION: DesktopSensorStation | None = None


def get_default_desktop_sensor_station() -> DesktopSensorStation:
    """Return the process-local desktop sensor station, creating it once.

    This accessor gives compatibility helper functions a persistent station without requiring eager construction during module import.
    """

    global _DEFAULT_DESKTOP_SENSOR_STATION
    if _DEFAULT_DESKTOP_SENSOR_STATION is None:
        _DEFAULT_DESKTOP_SENSOR_STATION = DesktopSensorStation()
    return _DEFAULT_DESKTOP_SENSOR_STATION


def psutil_readings() -> List[SensorReading]:
    """Collect desktop readings with psutil when available.

    The helper preserves the older function-style API while routing through the process-local station.
    """

    return get_default_desktop_sensor_station().psutil_readings()


def windows_readings() -> List[SensorReading]:
    """Return Windows desktop readings through the Python psutil path.

    The helper delegates to the stationed Windows sensor so non-Windows runtimes still receive a safe empty list.
    """

    return get_default_desktop_sensor_station().windows_readings()


def fallback_readings() -> List[SensorReading]:
    """Return portable fallback desktop readings.

    The helper delegates to the stationed fallback sensor and avoids recreating that object for each sample.
    """

    return get_default_desktop_sensor_station().fallback_readings()


def collect_readings() -> List[SensorReading]:
    """Return the best currently available desktop readings.

    The helper delegates to the stationed default selector so callers get psutil-first behavior with persistent sensor objects.
    """

    return get_default_desktop_sensor_station().collect_readings()


def readings_to_spatial_values(
    readings: Iterable[SensorReading],
) -> List[float]:
    """Return raw numeric values for downstream spatial placement.

    The helper keeps function-style projection compatible with callers that do not manage a station directly.
    """

    return get_default_desktop_sensor_station().readings_to_spatial_values(readings)
