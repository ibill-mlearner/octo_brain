"""Temperature sensor model."""

from __future__ import annotations

from typing import ClassVar, Tuple

from .base_sensor import BaseSensorModel


class TemperatureSensorModel(BaseSensorModel):
    """Model for thermal readings exposed by the runtime."""

    sensor_type: ClassVar[str] = "temperature"
    reading_prefixes: ClassVar[Tuple[str, ...]] = ("temperature_",)
    default_unit: ClassVar[str] = "C"
