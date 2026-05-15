"""Default wiring for desktop-sensor event polling.

This file provides the convenience constructor for the most common demo path. It connects the async sensor event system to the existing desktop sensor selector without adding polling logic to the root script. The function here is intentionally small because it is wiring code, not a new sensor implementation. Keeping default construction in this file makes it easy to add other preconfigured sensor event systems later.
"""

from __future__ import annotations

from sensors.desktops import DesktopSensor

from .sensor_event_system import SensorEventSystem


def build_default_sensor_event_system(
    interval_seconds: float = 1.0,
) -> SensorEventSystem:
    """Return an event system that polls the default desktop sensor reader.

    The caller receives a stopped system and can decide when to start, drain, and stop it.
    """

    event_system = SensorEventSystem()
    event_system.add_sensor(
        name="desktop",
        reader=DesktopSensor(),
        interval_seconds=interval_seconds,
    )
    return event_system
