"""Sensor-specific async event orchestration package.

This subpackage keeps sensor polling separate from the generic event queue so future event families can be added cleanly. It owns the poller, event-system manager, reader protocol, sensor-specific types, and default desktop wiring. The files under this package are intentionally focused on runtime coordination rather than sensor-probe implementation. Concrete probe logic still lives in the existing sensors package and is only called from here through reader objects.
"""

from .default_sensor_event_system import build_default_sensor_event_system
from .sensor_event_system import SensorEventSystem
from .sensor_poller import SensorPoller
from .sensor_reader import SensorReader
from .types import SensorReadingsProvider

__all__ = [
    "SensorEventSystem",
    "SensorPoller",
    "SensorReader",
    "SensorReadingsProvider",
    "build_default_sensor_event_system",
]
