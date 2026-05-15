"""Async poller that turns sensor-reader output into events.

This file contains the worker responsible for repeatedly calling one sensor-reading provider. The provider can remain synchronous because the poller runs it through ``asyncio.to_thread`` and then publishes event models back onto the queue. Startup, successful readings, errors, and shutdown are all represented as explicit event subclasses. Keeping the loop here isolates timing and error behavior from both the queue and concrete sensor implementations.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from models.events import (
    SensorPollerErrorEvent,
    SensorPollerStartedEvent,
    SensorPollerStoppedEvent,
    SensorReadingsEvent,
)

from ..async_event_queue import AsyncEventQueue
from .types import SensorReadingsProvider


@dataclass
class SensorPoller:
    """Repeatedly read one sensor provider and publish readings as events."""

    name: str
    reader: SensorReadingsProvider
    queue: AsyncEventQueue
    interval_seconds: float = 1.0

    async def run(
        self,
        stop_requested: asyncio.Event,
    ) -> None:
        """Poll until ``stop_requested`` is set.

        The loop reports lifecycle, reading, and error events so downstream consumers can understand what happened without sharing poller state.
        """

        await self.queue.publish_event(
            SensorPollerStartedEvent(
                source=self.name,
                interval_seconds=self.interval_seconds,
            )
        )

        while not stop_requested.is_set():
            started_at_utc = datetime.now(timezone.utc).isoformat()
            try:
                readings = list(await asyncio.to_thread(self.reader))
            except Exception as exc:  # noqa: BLE001 - errors become queue data.
                await self.queue.publish_event(
                    SensorPollerErrorEvent(
                        source=self.name,
                        error=exc,
                        started_at_utc=started_at_utc,
                    )
                )
            else:
                await self.queue.publish_event(
                    SensorReadingsEvent(
                        source=self.name,
                        readings=readings,
                        started_at_utc=started_at_utc,
                    )
                )

            try:
                await asyncio.wait_for(
                    stop_requested.wait(),
                    timeout=self.interval_seconds,
                )
            except TimeoutError:
                continue

        await self.queue.publish_event(SensorPollerStoppedEvent(source=self.name))
