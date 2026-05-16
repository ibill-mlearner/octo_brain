"""Base data model for node state snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar, Tuple

from .active_state_shape import ActiveStateShape

Vector3 = Tuple[float, float, float]
WindowSize = Tuple[int, int, int]


@dataclass(frozen=True)
class BaseNodeModel:
    """Structured data definition for shared node-local state."""

    model_type: ClassVar[str] = "node"

    node_id: str
    role: str
    channels: int = 8
    window_size: WindowSize = (10, 10, 10)
    learning_rate: float = 5e-4
    position: Vector3 = (0.0, 0.0, 0.0)
    velocity: Vector3 = (0.0, 0.0, 0.0)
    values_history: Tuple[float, ...] = field(default_factory=tuple)

    @property
    def active_state_shape(self) -> ActiveStateShape:
        """Return named dimensions for the node-local active state.

        This mirrors the runtime tensor created in node_roles/base_node.py:
        torch.zeros(1, config.channels, *config.window_size, device=self.device).
        The shape is derived from channels and window_size rather than loaded
        as independent configuration.
        """

        window_x, window_y, window_z = self.window_size

        return ActiveStateShape(
            batch_size=1,
            channels=self.channels,
            window_x=window_x,
            window_y=window_y,
            window_z=window_z,
        )

    def values(self) -> list[float]:
        """Return the numeric values associated with this node snapshot."""

        return list(self.values_history)

    def latest_value(self) -> float | None:
        """Return the latest associated value when one exists."""

        if not self.values_history:
            return None
        return self.values_history[-1]

    def to_json(self) -> dict[str, object]:
        """Return this node model in a JSON-friendly shape."""

        return {
            "model_type": self.model_type,
            "node_id": self.node_id,
            "role": self.role,
            "channels": self.channels,
            "window_size": list(self.window_size),
            "learning_rate": self.learning_rate,
            "position": list(self.position),
            "velocity": list(self.velocity),
            "active_state_shape": self.active_state_shape.to_json(),
            "values": self.values(),
        }

    @classmethod
    def from_json(
        cls,
        data: dict[str, Any],
    ) -> "BaseNodeModel":
        """Build a node model from a JSON-friendly mapping."""

        return cls(
            node_id=str(data["node_id"]),
            role=str(data["role"]),
            channels=int(data.get("channels", 8)),
            window_size=_int_tuple3(data.get("window_size", (10, 10, 10))),
            learning_rate=float(data.get("learning_rate", 5e-4)),
            position=_float_tuple3(data.get("position", (0.0, 0.0, 0.0))),
            velocity=_float_tuple3(data.get("velocity", (0.0, 0.0, 0.0))),
            values_history=tuple(
                float(value)
                for value in data.get("values", ())
            ),
        )


def _float_tuple3(values: object) -> Vector3:
    """Return a three-item float tuple from a JSON-friendly sequence."""

    first, second, third = values  # type: ignore[misc]
    return float(first), float(second), float(third)


def _int_tuple3(values: object) -> tuple[int, int, int]:
    """Return a three-item integer tuple from a JSON-friendly sequence."""

    first, second, third = values  # type: ignore[misc]
    return int(first), int(second), int(third)
