"""Actor node data model."""

from __future__ import annotations

from dataclasses import dataclass

from .base_node import BaseNodeModel


@dataclass(frozen=True)
class ActorNodeModel(BaseNodeModel):
    """Structured data definition for actor node state."""

    role: str = "actor"
