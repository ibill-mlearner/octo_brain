"""Sensor node data model."""

from __future__ import annotations

from dataclasses import dataclass

from .base_node import BaseNodeModel


@dataclass(frozen=True)
class SensorNodeModel(BaseNodeModel):
    """Structured data definition for sensor node state."""

    role: str = "sensor"
