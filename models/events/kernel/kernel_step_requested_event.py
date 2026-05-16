"""Data model for requested kernel-step events.

This event records the intent to run one kernel step. Its payload keeps only
step metadata, positions, optional summaries, and tensor metadata so queue
consumers can inspect the request without receiving the full persistent memory
field.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ._kernel_event_payload import build_kernel_step_payload
from ..base_event import BaseEvent


@dataclass(frozen=True, init=False)
class KernelStepRequestedEvent(BaseEvent):
    """Event emitted when a kernel step is requested."""

    def __init__(
        self,
        source: str,
        step_index: int,
        node_id: str | None = None,
        kernel_id: str | None = None,
        current_position: Any | None = None,
        next_position: Any | None = None,
        write_back: bool = True,
        error_summary: Any | None = None,
        surprise_summary: Any | None = None,
        tensor_summaries: Mapping[str, Any] | None = None,
    ) -> None:
        """Create a request event for a single kernel step."""

        super().__init__(
            event_type="kernel.step.requested",
            source=source,
            payload=build_kernel_step_payload(
                step_index=step_index,
                node_id=node_id,
                kernel_id=kernel_id,
                current_position=current_position,
                next_position=next_position,
                write_back=write_back,
                error_summary=error_summary,
                surprise_summary=surprise_summary,
                tensor_summaries=tensor_summaries,
            ),
        )
