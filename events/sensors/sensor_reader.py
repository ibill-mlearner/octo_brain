"""Protocol for sensor reader objects accepted by event pollers.

This file defines the minimal interface that the sensor event system needs from a reader object. It does not implement collection itself; concrete readers still live in the sensor modules. The protocol lets pollers accept either callable providers or objects with ``collect_readings`` while keeping type hints readable. Keeping the protocol in the sensor-event subpackage avoids mixing sensor assumptions into the generic queue layer.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from models.sensors import SensorReading


class SensorReader(Protocol):
    """Minimal reader shape accepted by the async sensor event system."""

    def collect_readings(self) -> Iterable[SensorReading]:
        """Return the current readings for one sensor source.

        Implementations may use any blocking or CPU-side collection mechanism as long as they return sensor-reading models.
        """
        ...
