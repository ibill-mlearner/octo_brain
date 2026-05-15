"""Shared type aliases for generic event orchestration.

This file contains only the type hints that belong to the broad event package rather than a specific event family. The current queue needs a handler type that can receive any ``BaseEvent`` subclass and optionally await work. Sensor-specific callable types are intentionally kept under ``events.sensors`` so future packages can define their own local conventions. Keeping these aliases small makes import dependencies predictable for the queue layer.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from models.events import BaseEvent


EventHandler = Callable[[BaseEvent], Awaitable[None] | None]
