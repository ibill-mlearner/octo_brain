"""Reflex node data model."""

from __future__ import annotations

from dataclasses import dataclass

from .base_node import BaseNodeModel


@dataclass(frozen=True)
class ReflexNodeModel(BaseNodeModel):
    """Structured data definition for reflex node state."""

    role: str = "reflex"
