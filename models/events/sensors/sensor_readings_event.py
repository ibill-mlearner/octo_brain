"""Data model for completed sensor-reading poll events.

This file defines the event emitted after a sensor reader successfully returns readings. It converts model-layer ``SensorReading`` instances into payload dictionaries that are easy for queue consumers to inspect or serialize. The event records both the count and the per-reading data so simple consumers can summarize without scanning the full list. Keeping this conversion in the model class keeps the poller focused on timing and error handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from models.sensors import SensorReading

from ..base_event import BaseEvent


@dataclass(frozen=True, init=False)
class SensorReadingsEvent(BaseEvent):
    """Event emitted after one sensor reader returns raw readings."""

    def __init__(
        self,
        source: str,
        readings: Iterable[SensorReading],
        started_at_utc: str,
    ) -> None:
        """Create a readings event from model-layer sensor readings.

        The payload stores the poll-start timestamp, total reading count, and normalized reading dictionaries.
        """

        reading_payloads = [
            self._sensor_reading_to_payload(reading)
            for reading in readings
        ]
        super().__init__(
            event_type="sensor.readings",
            source=source,
            payload={
                "started_at_utc": started_at_utc,
                "reading_count": len(reading_payloads),
                "readings": reading_payloads,
            },
        )

    def _sensor_reading_to_payload(
        self,
        reading: SensorReading,
    ) -> dict[str, Any]:
        """Convert a sensor reading into queue-friendly payload data.

        The returned dictionary preserves the reading's name, value, unit, source, collection method, and raw data.
        """

        return {
            "name": reading.name,
            "value": reading.value,
            "unit": reading.unit,
            "source": reading.source,
            "collection_method": reading.collection_method,
            "raw_data": reading.raw_data,
        }
