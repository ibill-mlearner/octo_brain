"""High-level holder for kernel-step event scheduling.

The kernel event system groups a ``SpatialMemorySystem`` step scheduler with the
async event queue that receives lifecycle events. It intentionally does not add
configuration to ``SpatialMemorySystem`` itself; queue sizing and runtime event
wiring belong at this orchestration layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..async_event_queue import AsyncEventQueue
from .kernel_step_scheduler import KernelStepScheduler

if TYPE_CHECKING:
    from tentacles.spatial_memory_system import SpatialMemorySystem


class KernelEventSystem:
    """Expose the queue and scheduler used for evented kernel steps."""

    def __init__(
        self,
        memory: SpatialMemorySystem,
        queue: AsyncEventQueue,
        source: str = "kernel.scheduler",
        node_id: str | None = None,
        kernel_id: str | None = None,
    ) -> None:
        """Create a kernel event system around existing memory and queue."""

        self.memory = memory
        self.queue = queue
        self.scheduler = KernelStepScheduler(
            memory=memory,
            queue=queue,
            source=source,
            node_id=node_id,
            kernel_id=kernel_id,
        )
