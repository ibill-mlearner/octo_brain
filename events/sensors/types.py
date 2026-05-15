"""Shared type aliases for sensor event orchestration.

This file contains the callable shape used by sensor pollers when they collect readings. It lives inside ``events.sensors`` because this type depends on sensor-reading models and should not leak into unrelated event families. The alias accepts ordinary blocking Python callables so existing CPU-side sensor probes do not need to become async-aware. Keeping it in one place also makes future reader signatures easier to evolve.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from models.sensors import SensorReading


SensorReadingsProvider = Callable[[], Iterable[SensorReading]]
