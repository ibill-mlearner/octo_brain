"""Data model for sensor-poller startup events.

This file defines the event emitted when a sensor poller begins running. It turns the poller's source name and interval into a consistent payload shape. The event type is fixed by the class so downstream consumers do not need to rely on repeated string construction at call sites. Keeping this small model separate leaves room for future startup metadata without changing the poller loop.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..base_event import BaseEvent


@dataclass(frozen=True, init=False)
class SensorPollerStartedEvent(BaseEvent):
    """Event emitted when one sensor poller starts running."""

    def __init__(
        self,
        source: str,
        interval_seconds: float,
    ) -> None:
        """Create a startup event for a named sensor poller.

        The interval is recorded in the payload so consumers can see the cadence that produced later readings.
        """

        super().__init__(
            event_type="sensor.poller.started",
            source=source,
            payload={"interval_seconds": interval_seconds},
        )
