"""Payload helpers for kernel-step event data models.

The helpers in this private module keep kernel event payloads compact and
serializable. They intentionally summarize tensor-like values instead of storing
large runtime tensors such as the persistent memory field.
"""

from __future__ import annotations

from collections.abc import Mapping
from numbers import Number
from typing import Any

from .tensor_summary import summarize_tensor


def build_kernel_step_payload(
    step_index: int,
    node_id: str | None,
    kernel_id: str | None,
    current_position: Any | None,
    next_position: Any | None,
    write_back: bool,
    error_summary: Any | None,
    surprise_summary: Any | None,
    tensor_summaries: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return the stable, lightweight payload shared by kernel-step events."""

    return {
        "step_index": step_index,
        "node_id": node_id,
        "kernel_id": kernel_id,
        "current_position": normalize_position(current_position),
        "next_position": normalize_position(next_position),
        "write_back": write_back,
        "error_summary": error_summary,
        "surprise_summary": surprise_summary,
        "tensor_summaries": normalize_tensor_summaries(tensor_summaries),
    }


def normalize_position(
    position: Any | None,
) -> Any | None:
    """Convert a position value into payload-friendly coordinates."""

    if position is None:
        return None

    if isinstance(position, Number):
        return position

    if hasattr(position, "detach"):
        position = position.detach()

    if hasattr(position, "cpu"):
        position = position.cpu()

    if hasattr(position, "tolist"):
        return position.tolist()

    if isinstance(position, tuple):
        return list(position)

    return position


def normalize_tensor_summaries(
    tensor_summaries: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Normalize tensor-like values into compact summaries keyed by name.

    The full persistent memory field is intentionally excluded from queued
    kernel events; callers should pass local patch or write summaries instead.
    """

    if tensor_summaries is None:
        return {}

    return {
        name: summarize_tensor(tensor)
        for name, tensor in tensor_summaries.items()
        if name != "memory_field"
    }
