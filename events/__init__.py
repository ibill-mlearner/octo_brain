"""Public doorway for asynchronous runtime event orchestration.

This package owns the general event queue pieces that are not tied to any one
event family. It also re-exports the current kernel and sensor event helpers so
the root demo and early callers have a short import path. Future event families
can live beside ``events.sensors`` without crowding this top-level namespace.
Keeping this file as an export surface avoids putting queue behavior or sensor
polling logic directly in package initialization.
"""

from .async_event_queue import AsyncEventQueue
from .kernel import (
    DEFAULT_KERNEL_EVENT_MAX_QUEUE_SIZE,
    KernelEventSystem,
    KernelEventWorker,
    KernelMovementModel,
    KernelStepSchedule,
    KernelStepScheduler,
    KernelTrainingObserver,
    build_default_kernel_event_system,
    publish_kernel_step_requests,
)
from .sensors import (
    SensorEventSystem,
    SensorPoller,
    SensorReader,
    build_default_sensor_event_system,
)

__all__ = [
    "AsyncEventQueue",
    "DEFAULT_KERNEL_EVENT_MAX_QUEUE_SIZE",
    "KernelEventSystem",
    "KernelEventWorker",
    "KernelMovementModel",
    "KernelStepSchedule",
    "KernelStepScheduler",
    "KernelTrainingObserver",
    "SensorEventSystem",
    "SensorPoller",
    "SensorReader",
    "build_default_kernel_event_system",
    "build_default_sensor_event_system",
    "publish_kernel_step_requests",
]
