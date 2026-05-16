"""Data model for completed kernel-step events.

This event records the observed result of one kernel step. Its payload includes
movement and write-back metadata plus optional surprise and tensor summaries,
while intentionally avoiding the full persistent memory field.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ._kernel_event_payload import build_kernel_step_payload
from ..base_event import BaseEvent


@dataclass(frozen=True, init=False)
class KernelStepCompletedEvent(BaseEvent):
    """Event emitted when a kernel step completes successfully."""

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
        active_state: Any | None = None,
        visible_patch: Any | None = None,
        memory_write: Any | None = None,
    ) -> None:
        """Create a completion event for a single kernel step."""

        super().__init__(
            event_type="kernel.step.completed",
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
                tensor_summaries=_completion_tensor_summaries(
                    tensor_summaries=tensor_summaries,
                    active_state=active_state,
                    visible_patch=visible_patch,
                    memory_write=memory_write,
                ),
            ),
        )


def _completion_tensor_summaries(
    tensor_summaries: Mapping[str, Any] | None,
    active_state: Any | None,
    visible_patch: Any | None,
    memory_write: Any | None,
) -> dict[str, Any]:
    """Merge common completion tensors into the compact summary mapping.

    The persistent ``memory_field`` is intentionally not accepted here because
    queue events should record local step context and writes, not the full field.
    """

    summaries = dict(tensor_summaries or {})

    if active_state is not None:
        summaries["active_state"] = active_state

    if visible_patch is not None:
        summaries["visible_patch"] = visible_patch

    if memory_write is not None:
        summaries["memory_write"] = memory_write

    return summaries
