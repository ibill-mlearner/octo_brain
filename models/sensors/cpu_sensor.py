"""CPU sensor model."""

from __future__ import annotations

from typing import ClassVar, Tuple

from .base_sensor import BaseSensorModel


class CpuSensorModel(BaseSensorModel):
    """Model for CPU usage readings."""

    sensor_type: ClassVar[str] = "cpu"
    reading_names: ClassVar[Tuple[str, ...]] = ("cpu_percent",)
    default_unit: ClassVar[str] = "%"
