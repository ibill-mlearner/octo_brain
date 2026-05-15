"""System-load sensor model."""

from __future__ import annotations

from typing import ClassVar, Tuple

from .base_sensor import BaseSensorModel


class LoadSensorModel(BaseSensorModel):
    """Model for standard-library load average readings."""

    sensor_type: ClassVar[str] = "load"
    reading_names: ClassVar[Tuple[str, ...]] = (
        "load_1m",
        "load_5m",
        "load_15m",
    )
    default_unit: ClassVar[str] = "load"
