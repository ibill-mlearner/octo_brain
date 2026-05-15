"""Decision node data model."""

from __future__ import annotations

from dataclasses import dataclass

from .base_node import BaseNodeModel


@dataclass(frozen=True)
class DecisionNodeModel(BaseNodeModel):
    """Structured data definition for decision node state."""

    role: str = "decision"
