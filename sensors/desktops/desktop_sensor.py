"""Default desktop sensor selection.

This file defines the desktop sensor class that chooses between the richer psutil path and the portable fallback path. It does not collect any readings directly; instead, it coordinates the two concrete sensors that own those collection details. The class can receive existing sensor instances so a station or polling loop can keep them alive in memory. If psutil returns readings, those values are used as the desktop sample. If psutil is unavailable or produces no readings, the standard-library fallback sensor supplies the sample.
"""

from __future__ import annotations

from typing import List

from models.sensors import SensorReading
from ..base_sensor import BaseSensor

from .fallback_sensor import DesktopFallbackSensor
from .psutil_sensor import DesktopPsutilSensor


class DesktopSensor(BaseSensor):
    """Choose the best available desktop reading source.

    The class keeps selection policy separate from the concrete psutil and fallback collection implementations.
    """

    name = "desktop"
    reading_names = (
        DesktopPsutilSensor.reading_names
        + DesktopFallbackSensor.reading_names
    )
    reading_prefixes = DesktopPsutilSensor.reading_prefixes
    source = "desktop"
    collection_method = "psutil_or_standard_library"

    def __init__(
        self,
        psutil_sensor: DesktopPsutilSensor | None = None,
        fallback_sensor: DesktopFallbackSensor | None = None,
    ) -> None:
        """Store the concrete desktop sensors used by the selector.

        Optional injected sensors let a station reuse long-lived objects instead of rebuilding them every time readings are collected.
        """

        self.psutil_sensor = psutil_sensor or DesktopPsutilSensor()
        self.fallback_sensor = fallback_sensor or DesktopFallbackSensor()

    def collect_readings(self) -> List[SensorReading]:
        """Collect psutil readings first, then fall back to portable readings.

        This preserves the previous best-available behavior while allowing the concrete sensors themselves to own platform details.
        """

        readings = self.psutil_sensor.collect_readings()
        if readings:
            return readings
        return self.fallback_sensor.collect_readings()
