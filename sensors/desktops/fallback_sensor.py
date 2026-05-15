"""Standard-library fallback desktop sensor collection.

This file defines the desktop sensor that works without optional third-party packages. It uses only Python standard-library calls so the sensor package can still emit safe numeric readings in minimal environments. The fallback currently reports load averages when the runtime exposes them and process time on every platform. It is intentionally smaller than the psutil-backed sensor because it should remain dependable when richer operating-system counters are unavailable. The readings still use the shared ``SensorReading`` model so downstream grouping and projection code can treat them like any other sensor sample.
"""

from __future__ import annotations

import os
import time
from typing import List

from models.sensors import SensorReading
from ..base_sensor import BaseSensor


class DesktopFallbackSensor(BaseSensor):
    """Collect standard-library desktop readings when psutil is unavailable.

    This class provides the portable lower-bound signal set for desktop sensor collection.
    """

    name = "desktop_fallback"
    reading_names = (
        "load_1m",
        "load_5m",
        "load_15m",
        "process_time",
    )
    source = "desktop"
    collection_method = "standard_library"

    def collect_readings(self) -> List[SensorReading]:
        """Collect the portable fallback readings.

        The method includes load averages only when the operating system exposes them and always adds process time as a minimal changing value.
        """

        readings: List[SensorReading] = []
        if hasattr(os, "getloadavg"):
            readings.extend(self._load_readings())
        readings.append(
            self.build_reading(
                "process_time",
                time.process_time(),
                "seconds",
                collection_method="time.process_time",
            )
        )
        return readings

    def _load_readings(self) -> List[SensorReading]:
        """Return system load averages from the standard library.

        Each average is converted into a named ``SensorReading`` so the load model can recognize one-, five-, and fifteen-minute values separately.
        """

        return [
            self.build_reading(
                label,
                value,
                "load",
                collection_method="os.getloadavg",
            )
            for label, value in zip(
                ("load_1m", "load_5m", "load_15m"),
                os.getloadavg(),
            )
        ]
