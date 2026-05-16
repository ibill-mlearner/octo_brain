"""Public doorway for asynchronous runtime event orchestration.

This package owns the general event queue pieces that are not tied to any one event family. It also re-exports the current sensor-event helpers so the root demo and early callers have a short import path. Future event families can live beside ``events.sensors`` without crowding this top-level namespace. Keeping this file as an export surface avoids putting queue behavior or sensor polling logic directly in package initialization.
"""

from .async_event_queue import AsyncEventQueue
from .kernel import (
    KernelMovementModel,
    KernelStepSchedule,
    KernelStepScheduler,
    publish_kernel_step_requests,
)
from .kernel import KernelEventWorker
from .sensors import (
    SensorEventSystem,
    SensorPoller,
    SensorReader,
    build_default_sensor_event_system,
)

__all__ = [
    "AsyncEventQueue",
    "KernelMovementModel",
    "KernelStepSchedule",
    "KernelStepScheduler",
    "publish_kernel_step_requests",
    "KernelEventWorker",
    "SensorEventSystem",
    "SensorPoller",
    "SensorReader",
    "build_default_sensor_event_system",
]
