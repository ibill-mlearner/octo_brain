"""Inspectable tensor summaries for kernel event payloads.

Kernel events should stay small enough for async queues and logs. The helper in
this module records tensor metadata and, for modest detached tensors, numeric
summary values without storing the complete tensor contents.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import torch

DEFAULT_MAX_STAT_ELEMENTS = 100_000
DEFAULT_PREVIEW_ELEMENTS = 0


def summarize_tensor(
    tensor: Any,
    preview_elements: int = DEFAULT_PREVIEW_ELEMENTS,
    max_stat_elements: int = DEFAULT_MAX_STAT_ELEMENTS,
) -> Any:
    """Return compact metadata and cheap scalar stats for a tensor-like value.

    Non tensor-like values are returned unchanged so callers can mix already
    prepared summaries with tensors in the same payload mapping. The full tensor
    is never copied into the result.
    """

    if tensor is None:
        return None

    if isinstance(tensor, Mapping):
        return dict(tensor)

    if not isinstance(tensor, torch.Tensor):
        return tensor

    detached = tensor.detach()
    summary: dict[str, Any] = {
        "shape": list(detached.shape),
        "dtype": str(detached.dtype),
        "device": str(detached.device),
        "numel": int(detached.numel()),
    }

    if _can_summarize_values(detached, max_stat_elements):
        summary.update(_numeric_stats(detached))

    if preview_elements > 0:
        preview = _preview(detached, preview_elements)
        if preview:
            summary["preview"] = preview

    return summary


def _can_summarize_values(
    tensor: torch.Tensor,
    max_stat_elements: int,
) -> bool:
    """Return whether numeric stats should be cheap and meaningful."""

    if tensor.numel() == 0:
        return False

    if tensor.numel() > max_stat_elements:
        return False

    if tensor.is_sparse:
        return False

    return (
        tensor.is_floating_point()
        or tensor.is_complex()
        or _is_integral_tensor(tensor)
    )


def _numeric_stats(
    tensor: torch.Tensor,
) -> dict[str, float]:
    """Return scalar stats for a detached tensor."""

    stat_tensor = tensor
    if tensor.is_complex():
        stat_tensor = tensor.abs()
    elif not tensor.is_floating_point():
        stat_tensor = tensor.to(torch.float32)

    return {
        "min": float(stat_tensor.min().item()),
        "max": float(stat_tensor.max().item()),
        "mean": float(stat_tensor.mean().item()),
        "std": float(stat_tensor.std(unbiased=False).item()),
    }


def _preview(
    tensor: torch.Tensor,
    preview_elements: int,
) -> list[Any]:
    """Return a small flattened preview list from a detached tensor."""

    values = tensor.flatten()[:preview_elements].cpu().tolist()
    if isinstance(values, list):
        return values
    return [values]


def _is_integral_tensor(
    tensor: torch.Tensor,
) -> bool:
    """Return whether a tensor dtype is an integer-like dtype."""

    return tensor.dtype in {
        torch.uint8,
        torch.int8,
        torch.int16,
        torch.int32,
        torch.int64,
    }
