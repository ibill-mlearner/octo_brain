"""Payload helpers for kernel-step event data models.

The helpers in this private module keep kernel event payloads compact and
serializable. They intentionally summarize tensor-like values instead of storing
large runtime tensors such as the persistent memory field.
"""

from __future__ import annotations

from collections.abc import Mapping
from numbers import Number
from typing import Any


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
    """Normalize tensor-like values into compact summaries keyed by name."""

    if tensor_summaries is None:
        return {}

    return {
        name: summarize_tensor(tensor)
        for name, tensor in tensor_summaries.items()
    }


def summarize_tensor(
    tensor: Any,
) -> Any:
    """Return metadata for tensor-like values without copying full contents."""

    if tensor is None:
        return None

    if isinstance(tensor, Mapping):
        return dict(tensor)

    summary: dict[str, Any] = {}

    shape = getattr(tensor, "shape", None)
    if shape is not None:
        summary["shape"] = list(shape)

    dtype = getattr(tensor, "dtype", None)
    if dtype is not None:
        summary["dtype"] = str(dtype)

    device = getattr(tensor, "device", None)
    if device is not None:
        summary["device"] = str(device)

    numel = _safe_numel(tensor)
    if numel is not None:
        summary["numel"] = numel

    if not summary:
        return tensor

    return summary


def _safe_numel(
    tensor: Any,
) -> int | None:
    """Return a tensor-like object's element count when cheaply available."""

    numel = getattr(tensor, "numel", None)
    if numel is None:
        return None

    if callable(numel):
        return int(numel())

    return int(numel)
