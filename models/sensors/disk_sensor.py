"""Disk sensor model."""

from __future__ import annotations

from typing import ClassVar, Tuple

from .base_sensor import BaseSensorModel


class DiskSensorModel(BaseSensorModel):
    """Model for disk usage and I/O readings."""

    sensor_type: ClassVar[str] = "disk"
    reading_names: ClassVar[Tuple[str, ...]] = (
        "disk_used_percent",
        "disk_read_bytes",
        "disk_write_bytes",
    )
