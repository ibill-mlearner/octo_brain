"""Memory sensor model."""

from __future__ import annotations

from typing import ClassVar, Tuple

from .base_sensor import BaseSensorModel


class MemorySensorModel(BaseSensorModel):
    """Model for memory capacity and usage readings."""

    sensor_type: ClassVar[str] = "memory"
    reading_names: ClassVar[Tuple[str, ...]] = (
        "memory_available",
        "memory_used_percent",
    )
