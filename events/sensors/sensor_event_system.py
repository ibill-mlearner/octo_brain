"""High-level manager for async sensor pollers.

This file owns the object that groups multiple sensor pollers around one shared event queue. It does not collect readings directly, but it creates and supervises the background asyncio tasks that run each poller. The class is useful for demos now and should also fit later runtime loops where AI work and sensor polling run side by side. Keeping this orchestration in one file makes the lifecycle of all sensor pollers easy to inspect.
"""

from __future__ import annotations

import asyncio

from ..async_event_queue import AsyncEventQueue
from .sensor_poller import SensorPoller
from .sensor_reader import SensorReader
from .types import SensorReadingsProvider


class SensorEventSystem:
    """Manage async sensor pollers that feed one shared event queue."""

    def __init__(
        self,
        queue: AsyncEventQueue | None = None,
    ) -> None:
        """Create a stopped event system.

        If no queue is supplied, the system owns a fresh in-memory event queue for all registered pollers.
        """

        self.queue = queue or AsyncEventQueue()
        self._pollers: list[SensorPoller] = []
        self._tasks: list[asyncio.Task[None]] = []
        self._stop_requested = asyncio.Event()

    def add_sensor(
        self,
        name: str,
        reader: SensorReadingsProvider | SensorReader,
        interval_seconds: float = 1.0,
    ) -> SensorPoller:
        """Register a sensor reader to be polled once the system starts.

        The reader can be a plain callable or an object with ``collect_readings`` so existing sensor classes can be reused directly.
        """

        if hasattr(reader, "collect_readings"):
            readings_provider = reader.collect_readings
        else:
            readings_provider = reader

        poller = SensorPoller(
            name=name,
            reader=readings_provider,
            queue=self.queue,
            interval_seconds=interval_seconds,
        )
        self._pollers.append(poller)
        return poller

    async def start(self) -> None:
        """Start all registered pollers as background asyncio tasks.

        Calling this on an already started system is a no-op so demos can safely guard setup paths.
        """

        if self._tasks:
            return

        self._stop_requested.clear()
        self._tasks = [
            asyncio.create_task(poller.run(self._stop_requested))
            for poller in self._pollers
        ]

    async def stop(self) -> None:
        """Request shutdown and wait for poller tasks to finish.

        Each poller receives the shared stop event and publishes its own stopped event before the task completes.
        """

        if not self._tasks:
            return

        self._stop_requested.set()
        await asyncio.gather(*self._tasks)
        self._tasks = []

    async def run_for(
        self,
        duration_seconds: float,
    ) -> None:
        """Run registered pollers for a finite demonstration window.

        This helper starts the system, sleeps for the requested duration, and always attempts a clean stop afterward.
        """

        await self.start()
        try:
            await asyncio.sleep(duration_seconds)
        finally:
            await self.stop()
