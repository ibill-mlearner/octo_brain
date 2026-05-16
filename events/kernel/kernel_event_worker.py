"""Async worker for serialized spatial-memory kernel steps.

The worker in this module is the single runtime owner of a
``SpatialMemorySystem`` instance and its mutable stepping state. Kernel step
requests arrive as events, but the worker keeps direct memory-field mutation
inside its own loop so unrelated event subscribers can observe step lifecycle
messages without writing to the persistent field concurrently.
"""

from __future__ import annotations

import asyncio
from typing import Any

import torch

from models.events import (
    BaseEvent,
    KernelStepCompletedEvent,
    KernelStepFailedEvent,
)
from tentacles.spatial_memory_system import SpatialMemorySystem

from ..async_event_queue import AsyncEventQueue


KERNEL_STEP_REQUESTED = "kernel.step.requested"


class KernelEventWorker:
    """Own and advance one ``SpatialMemorySystem`` from kernel-step events."""

    def __init__(
        self,
        memory_system: SpatialMemorySystem,
        active_state: torch.Tensor,
        position: torch.Tensor,
        event_queue: AsyncEventQueue,
        velocity: torch.Tensor | None = None,
        input_queue: asyncio.Queue[BaseEvent] | None = None,
        source: str = "kernel-event-worker",
        kernel_id: str | None = None,
    ) -> None:
        """Create a stopped worker around one spatial-memory system.

        If ``input_queue`` is omitted, the worker subscribes to the shared
        ``event_queue`` and mirrors ``kernel.step.requested`` events into a
        private kernel input queue. This lets other consumers still drain the
        shared queue while kernel stepping remains serialized here.
        """

        self.memory_system = memory_system
        self.active_state = active_state
        self.position = position
        self.velocity = velocity
        self.event_queue = event_queue
        self.source = source
        self.kernel_id = kernel_id
        self.input_queue = input_queue or asyncio.Queue()
        self._owns_input_subscription = input_queue is None

        if self._owns_input_subscription:
            self.event_queue.subscribe(
                KERNEL_STEP_REQUESTED,
                self.enqueue_requested_event,
            )

    def enqueue_requested_event(
        self,
        event: BaseEvent,
    ) -> None:
        """Mirror a requested step event into the worker input queue."""

        self.input_queue.put_nowait(event)

    async def run(
        self,
        stop_requested: asyncio.Event,
    ) -> None:
        """Process requested kernel steps until shutdown is requested.

        The loop waits briefly for input so a stop request can end the worker
        even when no kernel-step requests are arriving.
        """

        while not stop_requested.is_set():
            try:
                event = await asyncio.wait_for(
                    self.input_queue.get(),
                    timeout=0.1,
                )
            except TimeoutError:
                continue

            try:
                await self.handle_event(event)
            finally:
                self.input_queue.task_done()

    async def handle_event(
        self,
        event: BaseEvent,
    ) -> BaseEvent | None:
        """Handle one event and return the lifecycle event that was published."""

        if event.event_type != KERNEL_STEP_REQUESTED:
            return None

        return await self.step_from_event(event)

    async def step_from_event(
        self,
        event: BaseEvent,
    ) -> BaseEvent:
        """Run one spatial-memory step from a request event."""

        payload = event.payload
        step_index = int(payload.get("step_index", event.sequence))
        write_back = bool(payload.get("write_back", True))
        current_position = self.position

        try:
            updated_active, next_position, patch = self.memory_system.step(
                self.active_state,
                current_position,
                write_back=write_back,
            )
        except Exception as exc:  # noqa: BLE001 - failures are published events.
            return await self.event_queue.publish_event(
                KernelStepFailedEvent(
                    source=self.source,
                    step_index=step_index,
                    node_id=payload.get("node_id"),
                    kernel_id=self._event_kernel_id(payload),
                    current_position=current_position,
                    next_position=payload.get("next_position"),
                    write_back=write_back,
                    error_summary=self._summarize_exception(exc),
                    tensor_summaries=self._state_tensor_summaries(),
                )
            )

        previous_position = self.position
        self.active_state = updated_active
        self.position = next_position
        self.velocity = next_position - previous_position

        return await self.event_queue.publish_event(
            KernelStepCompletedEvent(
                source=self.source,
                step_index=step_index,
                node_id=payload.get("node_id"),
                kernel_id=self._event_kernel_id(payload),
                current_position=current_position,
                next_position=next_position,
                write_back=write_back,
                surprise_summary=payload.get("surprise_summary"),
                tensor_summaries={
                    **self._state_tensor_summaries(),
                    "read_patch": patch,
                },
            )
        )

    def _event_kernel_id(
        self,
        payload: dict[str, Any],
    ) -> str | None:
        """Prefer the request kernel id and fall back to the worker id."""

        return payload.get("kernel_id") or self.kernel_id

    def _state_tensor_summaries(self) -> dict[str, torch.Tensor]:
        """Return the current owned runtime tensors for event summarization."""

        summaries = {
            "active_state": self.active_state,
            "position": self.position,
        }
        if self.velocity is not None:
            summaries["velocity"] = self.velocity
        return summaries

    @staticmethod
    def _summarize_exception(
        exc: Exception,
    ) -> dict[str, str]:
        """Return a compact, serializable exception summary."""

        return {
            "type": type(exc).__name__,
            "message": str(exc),
        }

