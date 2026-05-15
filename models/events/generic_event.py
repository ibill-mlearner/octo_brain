"""Generic event data model for callers without a richer event subclass.

This file supplies the fallback event type used when callers only need an event type, source, and payload. It inherits from ``BaseEvent`` so the queue can handle it exactly like specialized events. Generic events are useful for early experiments and simple runtime signals before a dedicated model is worth creating. More structured event families should still prefer their own subclasses when they have stable payload expectations.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .base_event import BaseEvent
from .types import EventPayload


@dataclass(frozen=True)
class GenericEvent(BaseEvent):
    """Simple event carrying an explicit event type, source, and payload."""

    event_type: str
    source: str
    payload: EventPayload = field(default_factory=dict)
