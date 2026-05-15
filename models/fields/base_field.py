"""Base data model for spatial memory field snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar, Tuple

FieldSize = Tuple[int, int, int]
FieldShape = Tuple[int, int, int, int]


@dataclass(frozen=True)
class BaseFieldModel:
    """Structured data definition for persistent memory field state."""

    model_type: ClassVar[str] = "field"

    field_id: str = "base_field"
    channels: int = 8
    field_size: FieldSize = (100, 100, 100)
    device: str = "cpu"
    values_history: Tuple[float, ...] = field(default_factory=tuple)

    @property
    def field_shape(self) -> FieldShape:
        """Return the persistent memory field shape."""

        return (
            self.channels,
            *self.field_size,
        )

    def values(self) -> list[float]:
        """Return the numeric values associated with this field snapshot."""

        return list(self.values_history)

    def latest_value(self) -> float | None:
        """Return the latest associated value when one exists."""

        if not self.values_history:
            return None
        return self.values_history[-1]

    def to_json(self) -> dict[str, object]:
        """Return this field model in a JSON-friendly shape."""

        return {
            "model_type": self.model_type,
            "field_id": self.field_id,
            "channels": self.channels,
            "field_size": list(self.field_size),
            "field_shape": list(self.field_shape),
            "device": self.device,
            "values": self.values(),
        }

    @classmethod
    def from_json(
        cls,
        data: dict[str, Any],
    ) -> "BaseFieldModel":
        """Build a field model from a JSON-friendly mapping."""

        return cls(
            field_id=str(data.get("field_id", "base_field")),
            channels=int(data.get("channels", 8)),
            field_size=_int_tuple3(data.get("field_size", (100, 100, 100))),
            device=str(data.get("device", "cpu")),
            values_history=tuple(
                float(value)
                for value in data.get("values", ())
            ),
        )


def _int_tuple3(values: object) -> tuple[int, int, int]:
    """Return a three-item integer tuple from a JSON-friendly sequence."""

    first, second, third = values  # type: ignore[misc]
    return int(first), int(second), int(third)
