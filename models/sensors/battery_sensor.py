"""Battery sensor model."""

from __future__ import annotations

from typing import ClassVar, Tuple

from .base_sensor import BaseSensorModel


class BatterySensorModel(BaseSensorModel):
    """Model for battery percentage and remaining-time readings."""

    sensor_type: ClassVar[str] = "battery"
    reading_names: ClassVar[Tuple[str, ...]] = (
        "battery_percent",
        "battery_seconds_left",
    )
