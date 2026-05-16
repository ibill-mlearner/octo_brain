"""Async kernel-step scheduler that emits lifecycle events.

This module keeps event publishing beside the scheduler instead of inside
``SpatialMemorySystem``. The memory system stays focused on spatial reads,
writes, movement, and local update behavior, while this scheduler reports the
runtime lifecycle around each step.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from models.events import (
    KernelStepCompletedEvent,
    KernelStepFailedEvent,
    KernelStepRequestedEvent,
)

from ..async_event_queue import AsyncEventQueue

if TYPE_CHECKING:
    from tentacles.spatial_memory_system import SpatialMemorySystem


class KernelStepScheduler:
    """Run spatial-memory steps and publish kernel-step lifecycle events."""

    def __init__(
        self,
        memory: SpatialMemorySystem,
        queue: AsyncEventQueue,
        source: str = "kernel.scheduler",
        node_id: str | None = None,
        kernel_id: str | None = None,
    ) -> None:
        """Create a scheduler around one memory system and shared queue."""

        self.memory = memory
        self.queue = queue
        self.source = source
        self.node_id = node_id
        self.kernel_id = kernel_id
        self._step_index = 0

    async def step(
        self,
        active_state: Any,
        position: Any,
        write_back: bool = True,
    ) -> tuple[Any, Any, Any]:
        """Run one memory step and publish requested/completed/failed events.

        Event publication is awaited before producing the next state. When the
        queue is bounded, this lets normal queue backpressure slow step
        production without adding separate throttling logic.
        """

        step_index = self._step_index
        await self.queue.publish_event(
            KernelStepRequestedEvent(
                source=self.source,
                step_index=step_index,
                node_id=self.node_id,
                kernel_id=self.kernel_id,
                current_position=position,
                write_back=write_back,
            )
        )

        try:
            updated_active, next_position, patch = self.memory.step(
                active_state=active_state,
                position=position,
                write_back=write_back,
            )
        except Exception as error:
            await self.queue.publish_event(
                KernelStepFailedEvent(
                    source=self.source,
                    step_index=step_index,
                    node_id=self.node_id,
                    kernel_id=self.kernel_id,
                    current_position=position,
                    write_back=write_back,
                    error_summary={
                        "type": type(error).__name__,
                        "message": str(error),
                    },
                )
            )
            raise

        await self.queue.publish_event(
            KernelStepCompletedEvent(
                source=self.source,
                step_index=step_index,
                node_id=self.node_id,
                kernel_id=self.kernel_id,
                current_position=position,
                next_position=next_position,
                write_back=write_back,
                tensor_summaries={
                    "active_state": updated_active,
                    "patch": patch,
                },
            )
        )
        self._step_index += 1
        return updated_active, next_position, patch
