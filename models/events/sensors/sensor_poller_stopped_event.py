"""Data model for sensor-poller shutdown events.

This file defines the event emitted when a sensor poller exits its loop. The model has a fixed event type and an empty payload because the source name is enough for the first shutdown signal. It still exists as a distinct subclass so consumers can match lifecycle events through event types or class names. Future shutdown details can be added here without touching the queue implementation.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..base_event import BaseEvent


@dataclass(frozen=True, init=False)
class SensorPollerStoppedEvent(BaseEvent):
    """Event emitted when one sensor poller stops running."""

    def __init__(
        self,
        source: str,
    ) -> None:
        """Create a shutdown event for a named sensor poller.

        The payload is intentionally empty for now because the source field identifies which poller stopped.
        """

        super().__init__(
            event_type="sensor.poller.stopped",
            source=source,
            payload={},
        )
