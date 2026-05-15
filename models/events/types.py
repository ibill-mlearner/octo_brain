"""Shared type aliases for event model payloads.

This file defines payload-level typing for event data models. Payloads are intentionally flexible dictionaries because early events may carry different shapes while the system is still exploratory. More specific event subclasses can still normalize their own payload keys before passing them into the base event. Keeping the alias in the model package avoids importing orchestration code just to annotate event data.
"""

from __future__ import annotations

from typing import Any


EventPayload = dict[str, Any]
