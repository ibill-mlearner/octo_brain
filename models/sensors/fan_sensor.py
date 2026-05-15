"""Fan sensor model."""

from __future__ import annotations

from typing import ClassVar, Tuple

from .base_sensor import BaseSensorModel


class FanSensorModel(BaseSensorModel):
    """Model for fan-speed readings exposed by the runtime."""

    sensor_type: ClassVar[str] = "fan"
    reading_prefixes: ClassVar[Tuple[str, ...]] = ("fan_",)
    default_unit: ClassVar[str] = "rpm"
