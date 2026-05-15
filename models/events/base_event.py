"""Base event data model for queued runtime messages.

This file defines the common fields shared by every event object that can enter an async event queue. The base model stores routing information, payload data, creation time, and the queue-assigned sequence number. Specialized event classes inherit from this class so consumers can treat them polymorphically through one shared shape. The only behavior here is sequence-copying, which keeps queue metadata assignment out of individual event subclasses.
"""

from __future__ import annotations

from copy import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .types import EventPayload


@dataclass(frozen=True)
class BaseEvent:
    """Common immutable shape shared by all queued event data models."""

    event_type: str
    source: str
    payload: EventPayload = field(default_factory=dict)
    created_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    sequence: int = 0

    def with_sequence(
        self,
        sequence: int,
    ) -> "BaseEvent":
        """Return a copy of this event with a queue-local sequence number.

        The original event remains unchanged so callers can reuse or inspect the pre-queued model safely.
        """

        queued_event = copy(self)
        object.__setattr__(queued_event, "sequence", sequence)
        return queued_event
