"""Async queue orchestration for runtime events.

This file defines the generic queue that all event families can share. It is responsible for assigning queue-local sequence numbers, notifying subscribers, and storing events until consumers drain or retrieve them. It deliberately works with the base event model instead of sensor-specific types so it can support future event packages. The queue stays small and in-memory because this layer is intended for live runtime coordination rather than long-term persistence.
"""

from __future__ import annotations

import asyncio
from itertools import count

from models.events import BaseEvent, EventPayload, GenericEvent

from .types import EventHandler


class AsyncEventQueue:
    """Small asyncio event queue with optional type-based subscribers."""

    def __init__(
        self,
        max_queue_size: int = 0,
    ) -> None:
        """Create the queue and in-memory subscriber registry.

        ``max_queue_size=0`` keeps asyncio's default unbounded behavior, while a positive size lets callers choose backpressure.
        """

        self._queue: asyncio.Queue[BaseEvent] = asyncio.Queue(
            maxsize=max_queue_size
        )
        self._sequence_numbers = count(1)
        self._subscribers: dict[str, list[EventHandler]] = {}

    @property
    def pending_count(self) -> int:
        """Return the number of events waiting to be consumed.

        This is a lightweight inspection helper for demos, diagnostics, and simple runtime loops.
        """

        return self._queue.qsize()

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """Register a handler for an event type.

        The special ``"*"`` event type receives every published event before it is queued.
        """

        self._subscribers.setdefault(event_type, []).append(handler)

    async def publish(
        self,
        event_type: str,
        source: str,
        payload: EventPayload | None = None,
    ) -> BaseEvent:
        """Create a generic event, run subscribers, and enqueue it.

        Use this helper when the caller does not need a dedicated event-model subclass.
        """

        return await self.publish_event(
            GenericEvent(
                event_type=event_type,
                source=source,
                payload=payload or {},
            )
        )

    async def publish_event(
        self,
        event: BaseEvent,
    ) -> BaseEvent:
        """Assign a sequence number, run subscribers, and enqueue an event.

        The returned event is the queued copy, which keeps the original model object reusable by the caller.
        """

        queued_event = event.with_sequence(next(self._sequence_numbers))
        await self._dispatch(queued_event)
        await self._queue.put(queued_event)
        return queued_event

    async def get(self) -> BaseEvent:
        """Wait for and return the next queued event.

        This is the direct consumer path when a caller wants one event at a time.
        """

        return await self._queue.get()

    def task_done(self) -> None:
        """Mark the most recently consumed event as processed.

        This mirrors ``asyncio.Queue.task_done`` for callers that use ``get`` directly.
        """

        self._queue.task_done()

    async def drain(
        self,
        max_events: int,
        timeout_seconds: float = 0.1,
    ) -> list[BaseEvent]:
        """Return up to ``max_events`` currently available events.

        The first event may wait up to ``timeout_seconds``, and additional events are drained immediately to keep consumer loops responsive.
        """

        events = []
        if max_events <= 0:
            return events

        try:
            first_event = await asyncio.wait_for(
                self.get(),
                timeout=timeout_seconds,
            )
        except TimeoutError:
            return events

        events.append(first_event)
        self.task_done()

        while len(events) < max_events:
            try:
                event = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            events.append(event)
            self.task_done()

        return events

    async def _dispatch(
        self,
        event: BaseEvent,
    ) -> None:
        """Run exact-match and wildcard subscribers before queueing.

        Subscriber work happens before storage so observers can react to the same event object consumers later receive.
        """

        handlers = [
            *self._subscribers.get(event.event_type, []),
            *self._subscribers.get("*", []),
        ]
        for handler in handlers:
            result = handler(event)
            if result is not None:
                await result
