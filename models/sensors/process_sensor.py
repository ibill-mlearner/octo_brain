"""Process-time sensor model."""

from __future__ import annotations

from typing import ClassVar, Tuple

from .base_sensor import BaseSensorModel


class ProcessSensorModel(BaseSensorModel):
    """Model for process runtime readings."""

    sensor_type: ClassVar[str] = "process"
    reading_names: ClassVar[Tuple[str, ...]] = ("process_time",)
    default_unit: ClassVar[str] = "seconds"
