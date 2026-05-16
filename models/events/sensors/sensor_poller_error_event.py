"""Data model for sensor-poller failure events.

This file defines the event emitted when a sensor reader raises during a polling cycle. It preserves the exception type, message, and poll-start timestamp as queue payload data. The event lets the poller continue reporting failures without throwing exceptions into unrelated runtime consumers. Keeping errors as data also makes later logging or reflex behavior easier to attach through subscribers.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..base_event import BaseEvent


@dataclass(frozen=True, init=False)
class SensorPollerErrorEvent(BaseEvent):
    """Event emitted when a sensor reader raises during polling."""

    def __init__(
        self,
        source: str,
        error: Exception,
        started_at_utc: str,
    ) -> None:
        """Create an error event with exception details as payload data.

        The timestamp links the failure back to the polling attempt rather than the later queue-consumption time.
        """

        super().__init__(
            event_type="sensor.poller.error",
            source=source,
            payload={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "started_at_utc": started_at_utc,
            },
        )
