"""Default wiring for evented spatial-memory kernel steps.

This module owns the queue-size policy for kernel event demos. The default uses
a small bounded queue so live runtime demos cannot grow memory indefinitely if a
consumer falls behind. Use ``max_queue_size=0`` only for short local experiments
where asyncio's unbounded queue behavior is useful and the event volume is easy
to inspect. The scheduler awaits each ``publish_event(...)`` call, so bounded
queue backpressure naturally slows kernel-step production.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..async_event_queue import AsyncEventQueue
from .kernel_event_system import KernelEventSystem

if TYPE_CHECKING:
    from tentacles.spatial_memory_system import SpatialMemorySystem

DEFAULT_KERNEL_EVENT_MAX_QUEUE_SIZE = 32


def build_default_kernel_event_system(
    memory: SpatialMemorySystem,
    max_queue_size: int = DEFAULT_KERNEL_EVENT_MAX_QUEUE_SIZE,
    source: str = "kernel.scheduler",
    node_id: str | None = None,
    kernel_id: str | None = None,
) -> KernelEventSystem:
    """Return a stopped kernel event system with the default queue policy.

    ``max_queue_size`` defaults to a small bounded value for live runtime demos.
    Pass ``0`` only for short local experiments that intentionally want an
    unbounded queue. Kernel steps published through the scheduler await
    ``publish_event(...)``, so a full bounded queue applies backpressure before
    more steps are produced.
    """

    queue = AsyncEventQueue(max_queue_size=max_queue_size)
    return KernelEventSystem(
        memory=memory,
        queue=queue,
        source=source,
        node_id=node_id,
        kernel_id=kernel_id,
    )
