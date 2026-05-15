"""Network sensor model."""

from __future__ import annotations

from typing import ClassVar, Tuple

from .base_sensor import BaseSensorModel


class NetworkSensorModel(BaseSensorModel):
    """Model for network I/O readings."""

    sensor_type: ClassVar[str] = "network"
    reading_names: ClassVar[Tuple[str, ...]] = (
        "net_bytes_sent",
        "net_bytes_recv",
    )
